from dataclasses import dataclass, field
from typing import List, Any

@dataclass
class FaultEvent:
    time_offset: float
    action: str
    params: dict = field(default_factory=dict)


@dataclass
class Scenario:
    name: str
    num_nodes: int
    duration: float
    seed: int
    fault_events: List[FaultEvent] = field(default_factory=list)

# == PRE-BUILT SCENARIOS ==

# Stable Baseline: 5 nodes, no faults, run for 60 seconds
stable_baseline = Scenario(
    name="Stable Baseline",
    num_nodes=5,
    duration=60.0,
    seed=5546,
    fault_events=[]
)
 
# Single Node Crash: 5 nodes, one node crashes at 20s and recovers at 40s, run for 60 seconds
single_node_crash = Scenario(
    name="Single Node Crash",
    num_nodes=5,
    duration=60.0,
    seed=5546,
    fault_events=[
        FaultEvent(time_offset=20.0, action="crash", params={"node_id": 'node-1'}),
        FaultEvent(time_offset=40.0, action="recover", params={"node_id": 'node-1'})
    ]
)
 
# Rolling Crash: 5 nodes, 3 nodes crash at different times, run for 90 seconds
rolling_crash = Scenario(
    name="Rolling Crash",
    num_nodes=5,
    duration=90.0,
    seed=5546,
    fault_events=[
        FaultEvent(time_offset=15.0, action="crash", params={"node_id": 'node-2'}),
        FaultEvent(time_offset=30.0, action="crash", params={"node_id": 'node-3'}),
        FaultEvent(time_offset=45.0, action="crash", params={"node_id": 'node-4'})
    ]
)
 
# Moderate Congestion: 5 nodes, moderate delay and low packet loss from 25s to 55s, run for 80 seconds
moderate_congestion = Scenario(
    name="Moderate Congestion",
    num_nodes=5,
    duration=80.0,
    seed=5546,
    fault_events=[
        FaultEvent(time_offset=25.0, action="set_congestion", params={"delay": 0.075, "jitter": 0.025, "loss_rate": 0.05}),
        FaultEvent(time_offset=55.0, action="clear_congestion", params={})
    ]
)
 
# Moderate Congestion with Crash: same as moderate congestion, one node crashes mid-congestion at 40s, run for 80 seconds
moderate_congestion_with_crash = Scenario(
    name="Moderate Congestion with Crash",
    num_nodes=5,
    duration=80.0,
    seed=5546,
    fault_events=[
        FaultEvent(time_offset=25.0, action="set_congestion", params={"delay": 0.075, "jitter": 0.025, "loss_rate": 0.05}),
        FaultEvent(time_offset=40.0, action="crash", params={"node_id": 'node-5'}),
        FaultEvent(time_offset=55.0, action="clear_congestion", params={})
    ]
)
 
# High Congestion: 5 nodes, high network congestion from 25s to 55s, run for 80 seconds
high_congestion = Scenario(
    name="High Congestion",
    num_nodes=5,
    duration=80.0,
    seed=5546,
    fault_events=[
        FaultEvent(time_offset=25.0, action="set_congestion", params={"delay": 0.2, "jitter": 0.05, "loss_rate": 0.1}),
        FaultEvent(time_offset=55.0, action="clear_congestion", params={})
    ]
)
 
# High Congestion with Crash: 5 nodes, high congestion from 25s to 55s and one node crashes at 40s, run for 80 seconds
high_congestion_with_crash = Scenario(
    name="High Congestion with Crash",
    num_nodes=5,
    duration=80.0,
    seed=5546,
    fault_events=[
        FaultEvent(time_offset=25.0, action="set_congestion", params={"delay": 0.2, "jitter": 0.05, "loss_rate": 0.1}),
        FaultEvent(time_offset=40.0, action="crash", params={"node_id": 'node-5'}),
        FaultEvent(time_offset=55.0, action="clear_congestion", params={})
    ]
)
 
# Heavy Congestion: 5 nodes, heavy delay, high jitter, and significant packet loss from 25s to 55s, run for 80 seconds
heavy_congestion = Scenario(
    name="Heavy Congestion",
    num_nodes=5,
    duration=80.0,
    seed=5546,
    fault_events=[
        FaultEvent(time_offset=25.0, action="set_congestion", params={"delay": 0.35, "jitter": 0.15, "loss_rate": 0.2}),
        FaultEvent(time_offset=55.0, action="clear_congestion", params={})
    ]
)
 
# Heavy Congestion with Crash: same as heavy congestion, one node crashes mid-congestion at 40s, run for 80 seconds
heavy_congestion_with_crash = Scenario(
    name="Heavy Congestion with Crash",
    num_nodes=5,
    duration=80.0,
    seed=5546,
    fault_events=[
        FaultEvent(time_offset=25.0, action="set_congestion", params={"delay": 0.35, "jitter": 0.15, "loss_rate": 0.2}),
        FaultEvent(time_offset=40.0, action="crash", params={"node_id": 'node-5'}),
        FaultEvent(time_offset=55.0, action="clear_congestion", params={})
    ]
)
 
# Spike and Recovery: 5 nodes, short burst of heavy congestion from 20s to 35s then clears, run for 70 seconds
spike_and_recovery = Scenario(
    name="Spike and Recovery",
    num_nodes=5,
    duration=70.0,
    seed=5546,
    fault_events=[
        FaultEvent(time_offset=20.0, action="set_congestion", params={"delay": 0.35, "jitter": 0.15, "loss_rate": 0.2}),
        FaultEvent(time_offset=35.0, action="clear_congestion", params={})
    ]
)
 
# Spike and Recovery with Crash: same spike, one node crashes during the spike at 25s, run for 70 seconds
spike_and_recovery_with_crash = Scenario(
    name="Spike and Recovery with Crash",
    num_nodes=5,
    duration=70.0,
    seed=5546,
    fault_events=[
        FaultEvent(time_offset=20.0, action="set_congestion", params={"delay": 0.35, "jitter": 0.15, "loss_rate": 0.2}),
        FaultEvent(time_offset=25.0, action="crash", params={"node_id": 'node-5'}),
        FaultEvent(time_offset=35.0, action="clear_congestion", params={})
    ]
)