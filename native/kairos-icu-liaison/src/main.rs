#![forbid(unsafe_code)]
//! Experimental, synthetic-only ICU one-bed native consumer of Kairos staged DES.
//! Kairos owns all scheduling, resource queuing and lease-promotion semantics.
//! This thin application owns ONLY its parameter/admission and output mapping.

use std::collections::HashSet;
use std::env;
use std::fs;
use std::process::ExitCode;

use kairo_ecs_des::{StagedRequestState, StagedResourceRuntime};
use kairo_ecs_types::SimTime;
use serde::{Deserialize, Serialize};

const PROVIDER_SHA: &str = "273bf44956dfadd31336a9f9f645eba6b39779f9";
const PRODUCER: &str = "icu-liaison-kairos-consumer";
const MAX_REQUESTS: usize = 1000;

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
struct Input {
    schema_version: u32,
    data_class: String,
    scenario_id: String,
    seed: u64,
    horizon_minutes: u64,
    staffed_beds: u64,
    strategies: Vec<StrategyInput>,
    arrivals: Vec<Arrival>,
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
struct StrategyInput {
    strategy_id: String,
    initial_departure_minute: u64,
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
struct Arrival {
    request_id: String,
    request_minute: u64,
    occupied_duration_minutes: u64,
}

#[derive(Serialize)]
struct Provider {
    repository: &'static str,
    source_commit: &'static str,
    api: &'static str,
}

#[derive(Serialize)]
struct Window {
    start_minute: u64,
    end_minute: u64,
    staffed_beds: u64,
}

#[derive(Serialize)]
struct Occupancy {
    episode_id: String,
    start_minute: u64,
    end_minute: u64,
}

#[derive(Serialize)]
struct Request {
    request_id: String,
    request_minute: u64,
    disposition: &'static str,
    admitted_minute: Option<u64>,
}

#[derive(Serialize)]
struct Arm {
    strategy_id: String,
    occupancies: Vec<Occupancy>,
    requests: Vec<Request>,
}

#[derive(Serialize)]
struct Output {
    schema_version: u32,
    source_engine: &'static str,
    data_class: &'static str,
    producer: &'static str,
    producer_contract_version: &'static str,
    provider: Provider,
    scenario_id: String,
    seed: u64,
    horizon_minutes: u64,
    capacity: Vec<Window>,
    strategies: Vec<Arm>,
}

fn is_synthetic_id(value: &str) -> bool {
    let Some(rest) = value.strip_prefix("syn-") else {
        return false;
    };
    (1..=80).contains(&rest.len())
        && rest
            .bytes()
            .all(|b| b.is_ascii_lowercase() || b.is_ascii_digit() || b == b'-' || b == b'_')
}

fn is_strategy_id(value: &str) -> bool {
    let bytes = value.as_bytes();
    (2..=49).contains(&bytes.len())
        && bytes[0].is_ascii_lowercase()
        && bytes
            .iter()
            .all(|b| b.is_ascii_lowercase() || b.is_ascii_digit() || *b == b'_')
}

fn check(input: &Input) -> Result<(), String> {
    if input.schema_version != 1
        || input.data_class != "synthetic"
        || input.staffed_beds != 1
        || !(2..=525_600).contains(&input.horizon_minutes)
        || !input.scenario_id.starts_with("syn-")
        || input.scenario_id.len() > 128
        || !input
            .scenario_id
            .bytes()
            .all(|b| b.is_ascii_lowercase() || b.is_ascii_digit() || b == b'-' || b == b'_')
    {
        return Err("invalid synthetic scenario contract".into());
    }
    if !(2..=8).contains(&input.strategies.len())
        || input.strategies[0].strategy_id != "current_care"
    {
        return Err("current_care and at least one alternative required".into());
    }
    let mut names = HashSet::new();
    for arm in &input.strategies {
        if !is_strategy_id(&arm.strategy_id)
            || !names.insert(&arm.strategy_id)
            || arm.initial_departure_minute == 0
            || arm.initial_departure_minute > input.horizon_minutes
        {
            return Err("invalid strategy or resident departure".into());
        }
    }
    if input.arrivals.is_empty() || input.arrivals.len() > MAX_REQUESTS {
        return Err("unbounded or missing admission requests".into());
    }
    let mut requests = HashSet::new();
    for arrival in &input.arrivals {
        if !is_synthetic_id(&arrival.request_id)
            || !requests.insert(&arrival.request_id)
            || arrival.request_id == "syn-index-1"
            || arrival.request_minute >= input.horizon_minutes
            || arrival.occupied_duration_minutes == 0
        {
            return Err("invalid or duplicated synthetic demand request".into());
        }
    }
    Ok(())
}

fn simulate_arm(input: &Input, arm: &StrategyInput) -> Result<Arm, String> {
    let mut runtime = StagedResourceRuntime::new().map_err(|e| format!("native runtime: {e:?}"))?;
    let resource = runtime
        .create_resource(1)
        .map_err(|e| format!("resource: {e:?}"))?;
    let resident = runtime
        .spawn_actor()
        .map_err(|e| format!("resident: {e:?}"))?;
    let index = runtime
        .submit(resource, resident, SimTime::ZERO)
        .map_err(|e| format!("resident submit: {e:?}"))?;
    let events = runtime
        .run_for(1)
        .map_err(|e| format!("resident dispatch: {e:?}"))?;
    if events != 1 {
        return Err("resident admission not dispatched".into());
    }
    let original = runtime
        .request(index)
        .map_err(|e| format!("resident snapshot: {e:?}"))?;
    if original.state != StagedRequestState::Active {
        return Err("resident was not allocated the ICU bed".into());
    }
    if arm.initial_departure_minute < input.horizon_minutes {
        runtime
            .release(
                original.lease.ok_or("missing resident lease")?,
                SimTime::from_ticks(u128::from(arm.initial_departure_minute)),
            )
            .map_err(|e| format!("resident release: {e:?}"))?;
    }

    let mut admitted = vec![None; input.arrivals.len()];
    let mut handles = Vec::with_capacity(input.arrivals.len());
    for arrival in &input.arrivals {
        let actor = runtime
            .spawn_actor()
            .map_err(|e| format!("demand actor: {e:?}"))?;
        handles.push(
            runtime
                .submit(
                    resource,
                    actor,
                    SimTime::from_ticks(u128::from(arrival.request_minute)),
                )
                .map_err(|e| format!("demand submission: {e:?}"))?,
        );
    }
    let mut occupancies = vec![Occupancy {
        episode_id: "syn-index-1".into(),
        start_minute: 0,
        end_minute: arm.initial_departure_minute,
    }];
    // Kairos is the SOLE scheduler. Poll the post-dispatch staged request state;
    // each newly activated lease schedules its own later release in Kairos.
    let max_events = 2 * input.arrivals.len() + 2;
    for _ in 0..max_events {
        let dispatched = runtime
            .run_for(1)
            .map_err(|e| format!("native step: {e:?}"))?;
        if dispatched == 0 {
            break;
        }
        let now = u64::try_from(runtime.now().ticks())
            .map_err(|_| "simulation timestamp overflow".to_string())?;
        if now >= input.horizon_minutes {
            return Err("native event unexpectedly reached or passed horizon".into());
        }
        for (idx, handle) in handles.iter().enumerate() {
            if admitted[idx].is_some() {
                continue;
            }
            let snapshot = runtime
                .request(*handle)
                .map_err(|e| format!("native request: {e:?}"))?;
            if snapshot.state != StagedRequestState::Active {
                continue;
            }
            let arrival = &input.arrivals[idx];
            let finish = now
                .saturating_add(arrival.occupied_duration_minutes)
                .min(input.horizon_minutes);
            if finish <= now {
                return Err("invalid native occupancy interval".into());
            }
            admitted[idx] = Some(now);
            occupancies.push(Occupancy {
                episode_id: arrival.request_id.clone(),
                start_minute: now,
                end_minute: finish,
            });
            if finish < input.horizon_minutes {
                runtime
                    .release(
                        snapshot.lease.ok_or("missing demand lease")?,
                        SimTime::from_ticks(u128::from(finish)),
                    )
                    .map_err(|e| format!("demand lease release: {e:?}"))?;
            }
        }
    }
    if runtime
        .run_for(1)
        .map_err(|e| format!("bounded event drain: {e:?}"))?
        != 0
    {
        return Err("too many native events; refusal rather than partial output".into());
    }
    let mut requests = Vec::with_capacity(input.arrivals.len());
    for (i, arrival) in input.arrivals.iter().enumerate() {
        requests.push(Request {
            request_id: arrival.request_id.clone(),
            request_minute: arrival.request_minute,
            disposition: if admitted[i].is_some() {
                "admitted"
            } else {
                "censored"
            },
            admitted_minute: admitted[i],
        });
    }
    Ok(Arm {
        strategy_id: arm.strategy_id.clone(),
        occupancies,
        requests,
    })
}

fn run(input: Input) -> Result<Output, String> {
    check(&input)?;
    let mut strategies = Vec::new();
    for arm in &input.strategies {
        strategies.push(simulate_arm(&input, arm)?);
    }
    Ok(Output {
        schema_version: 1,
        source_engine: "kairos",
        data_class: "synthetic",
        producer: PRODUCER,
        producer_contract_version: "0.1.0",
        provider: Provider {
            repository: "https://github.com/edithatogo/kairos",
            source_commit: PROVIDER_SHA,
            api: "kairo-ecs-des::StagedResourceRuntime",
        },
        scenario_id: input.scenario_id,
        seed: input.seed,
        horizon_minutes: input.horizon_minutes,
        capacity: vec![Window {
            start_minute: 0,
            end_minute: input.horizon_minutes,
            staffed_beds: input.staffed_beds,
        }],
        strategies,
    })
}

fn main() -> ExitCode {
    let mut argv = env::args().skip(1);
    let Some(path) = argv.next() else {
        eprintln!("Usage: icu-liaison-kairos-consumer <synthetic-scenario.json>");
        return ExitCode::FAILURE;
    };
    if argv.next().is_some() {
        eprintln!("Exactly one versioned synthetic input is required");
        return ExitCode::FAILURE;
    }
    let output = fs::read_to_string(path)
        .map_err(|_| "cannot read synthetic input".to_string())
        .and_then(|bytes| {
            serde_json::from_str::<Input>(&bytes).map_err(|_| "invalid synthetic JSON".to_string())
        })
        .and_then(run)
        .and_then(|value| {
            serde_json::to_string(&value).map_err(|_| "cannot serialize native result".to_string())
        });
    match output {
        Ok(out) => {
            println!("{out}");
            ExitCode::SUCCESS
        }
        Err(message) => {
            eprintln!("P6 native consumer refused source or runtime: {message}");
            ExitCode::FAILURE
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn fixture() -> Input {
        serde_json::from_str(include_str!(
            "../../../model-inputs/p6/kairos-synthetic-input.json"
        ))
        .expect("synthetic contract fixture must parse")
    }

    #[test]
    fn bounded_kairos_staging_agrees_with_independent_one_bed_oracle() {
        let output = run(fixture()).expect("native scenario should execute");
        assert_eq!(output.strategies.len(), 2);
        assert_eq!(output.strategies[0].occupancies.len(), 2);
        assert_eq!(output.strategies[1].occupancies.len(), 2);
        assert_eq!(output.strategies[0].occupancies[1].start_minute, 120);
        assert_eq!(output.strategies[1].occupancies[1].start_minute, 90);
        assert_eq!(output.strategies[0].requests[0].admitted_minute, Some(120));
        assert_eq!(output.strategies[1].requests[0].admitted_minute, Some(90));
    }

    #[test]
    fn malformed_input_cannot_emit_a_valid_scenario() {
        let mut scenario = fixture();
        scenario.data_class = "observed".into();
        assert!(run(scenario).is_err());
    }

    #[test]
    fn horizon_censoring_does_not_create_a_ghost_bed() {
        let mut scenario = fixture();
        for arm in &mut scenario.strategies {
            arm.initial_departure_minute = scenario.horizon_minutes;
        }
        let output = run(scenario).expect("censored synthetic demand is valid");
        assert_eq!(output.strategies[0].occupancies.len(), 1);
        assert_eq!(output.strategies[0].requests[0].disposition, "censored");
    }

    #[test]
    fn queued_multiple_requests_conserve_one_bed_and_censor_at_horizon() {
        let mut scenario = fixture();
        scenario.arrivals[0].occupied_duration_minutes = 200;
        scenario.arrivals.push(Arrival {
            request_id: "syn-demand-2".into(),
            request_minute: 100,
            occupied_duration_minutes: 200,
        });
        let result = run(scenario).expect("bounded one-bed queue should execute");
        let first = &result.strategies[0];
        assert_eq!(first.requests.len(), 2);
        assert_eq!(first.requests[0].admitted_minute, Some(120));
        assert_eq!(first.requests[1].disposition, "censored");
        assert_eq!(first.occupancies[1].end_minute, 240);
    }

    #[test]
    fn duplicate_or_unbounded_requests_fail_closed() {
        let mut scenario = fixture();
        scenario.arrivals.push(Arrival {
            request_id: "syn-demand-1".into(),
            request_minute: 70,
            occupied_duration_minutes: 10,
        });
        assert!(run(scenario).is_err());
        let mut scenario = fixture();
        scenario.staffed_beds = 2;
        assert!(run(scenario).is_err());
    }
}
