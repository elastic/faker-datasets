import re
from pathlib import Path

import pytest
from faker import Faker

from faker_datasets import Provider, add_dataset, with_datasets, with_match


@pytest.fixture
def alerts_dataset():
    return Path(__file__).parent / "testdata" / "alerts.json"


@pytest.fixture
def fake(request, alerts_dataset):
    @add_dataset("alerts", alerts_dataset, picker="alert", root=".hits.hits[]._source")
    class TestProvider(Provider):
        @with_datasets("alerts")
        @with_match(lambda x: re.search("microsoft", x["kibana.alert.rule.name"], re.I))
        def microsoft_rule_names(self, alerts):
            alert = self.__pick__(alerts)
            return {"kibana.alert.rule.name": alert["kibana.alert.rule.name"]}

    fake = Faker()
    fake.add_provider(TestProvider)
    fake.seed_instance(request.node.name)
    return fake


def test_alerts(fake):
    maxDiff = None
    for item in [
        {
            "@timestamp": "2022-12-23T10:39:44.298Z",
            "event.category": ["process"],
            "event.kind": "signal",
            "event.type": ["start"],
            "kibana.alert.ancestors": [
                {"depth": 0, "id": "992OPoUBe3tySuKqpz9d", "index": "geneve-ut-292", "type": "event"},
            ],
            "kibana.alert.depth": 1,
            "kibana.alert.original_event.category": ["process"],
            "kibana.alert.original_event.type": ["start"],
            "kibana.alert.original_time": "2022-12-23T10:36:43.160Z",
            "kibana.alert.reason": "process event with process bash, parent process nawk, "
            "created medium alert Linux Restricted Shell Breakout "
            "via awk Commands.",
            "kibana.alert.risk_score": 47,
            "kibana.alert.rule.actions": [],
            "kibana.alert.rule.author": [],
            "kibana.alert.rule.category": "Event Correlation Rule",
            "kibana.alert.rule.consumer": "siem",
            "kibana.alert.rule.created_at": "2022-12-23T10:37:19.096Z",
            "kibana.alert.rule.created_by": "elastic",
            "kibana.alert.rule.description": "Identifies Linux binary awk abuse to "
            "breakout out of restricted shells or "
            "environments by spawning an interactive "
            "system\n"
            "shell. The awk utility is a text processing "
            "language used for data extraction and "
            "reporting tools and the activity of\n"
            "spawning shell is not a standard use of "
            "this binary for a user or system "
            "administrator. It indicates a potentially\n"
            "malicious actor attempting to improve the "
            "capabilities or stability of their "
            "access.\n",
            "kibana.alert.rule.enabled": True,
            "kibana.alert.rule.exceptions_list": [],
            "kibana.alert.rule.execution.uuid": "952487e5-365e-49bb-8513-be08c74b5e0b",
            "kibana.alert.rule.false_positives": [],
            "kibana.alert.rule.from": "now-2h",
            "kibana.alert.rule.immutable": False,
            "kibana.alert.rule.interval": "3s",
            "kibana.alert.rule.max_signals": 200,
            "kibana.alert.rule.name": "Linux Restricted Shell Breakout via awk Commands",
            "kibana.alert.rule.parameters": {
                "author": [],
                "description": "Identifies Linux binary awk abuse to breakout out of restricted shells or "
                "environments by spawning an interactive system\nshell. The awk utility is a "
                "text processing language used for data extraction and reporting tools and the "
                "activity of\nspawning shell is not a standard use of this binary for a user or system "
                "administrator. It indicates a potentially\nmalicious actor attempting "
                "to improve the capabilities or stability of their access.\n",
                "exceptions_list": [],
                "false_positives": [],
                "from": "now-2h",
                "immutable": False,
                "index": ["geneve-ut-292"],
                "language": "eql",
                "max_signals": 200,
                "query": "process where event.type == "
                '"start" and process.name in ("sh", '
                '"bash", "dash") and\n'
                '  process.parent.name in ("nawk", '
                '"mawk", "awk", "gawk") and '
                'process.parent.args : "BEGIN '
                '{system(*)}"\n',
                "references": [],
                "risk_score": 47,
                "risk_score_mapping": [],
                "rule_id": "10754992-28c7-4472-be5b-f3770fd04f2d",
                "severity": "medium",
                "severity_mapping": [],
                "threat": [],
                "to": "now",
                "type": "eql",
                "version": 1,
            },
            "kibana.alert.rule.producer": "siem",
            "kibana.alert.rule.references": [],
            "kibana.alert.rule.risk_score": 47,
            "kibana.alert.rule.risk_score_mapping": [],
            "kibana.alert.rule.rule_id": "10754992-28c7-4472-be5b-f3770fd04f2d",
            "kibana.alert.rule.rule_type_id": "siem.eqlRule",
            "kibana.alert.rule.severity": "medium",
            "kibana.alert.rule.severity_mapping": [],
            "kibana.alert.rule.tags": [],
            "kibana.alert.rule.threat": [],
            "kibana.alert.rule.to": "now",
            "kibana.alert.rule.type": "eql",
            "kibana.alert.rule.updated_at": "2022-12-23T10:37:19.096Z",
            "kibana.alert.rule.updated_by": "elastic",
            "kibana.alert.rule.uuid": "c55330b0-82ad-11ed-93ff-3323f74f31a3",
            "kibana.alert.rule.version": 1,
            "kibana.alert.severity": "medium",
            "kibana.alert.status": "active",
            "kibana.alert.uuid": "ddedd6a6c4ea61648972971f5602f024e16dd3f3d1f190ba1d1746e46e5129cc",
            "kibana.alert.workflow_status": "open",
            "kibana.space_ids": ["default"],
            "kibana.version": "8.2.0",
            "process": {"name": "bash", "parent": {"args": ["BEGIN {system(*)}"], "name": "nawk"}},
        },
    ]:
        assert item == fake.alert()

    for item in [
        {"kibana.alert.rule.name": "Microsoft 365 Potential ransomware activity"},
        {"kibana.alert.rule.name": "Microsoft Build Engine Loading Windows Credential Libraries"},
        {"kibana.alert.rule.name": "Microsoft 365 Exchange Management Group Role Assignment"},
        {"kibana.alert.rule.name": "Microsoft IIS Service Account Password Dumped"},
        {"kibana.alert.rule.name": "Process Injection by the Microsoft Build Engine"},
        {"kibana.alert.rule.name": "Microsoft 365 Exchange Safe Link Policy Disabled"},
        {"kibana.alert.rule.name": "Microsoft Exchange Worker Spawning Suspicious Processes"},
    ]:
        assert item == fake.microsoft_rule_names()
