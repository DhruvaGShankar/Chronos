"""
Business Invariant Rules & Declarative Event Schedule Builder v2.1.
Supports schema-qualified table names (e.g. sch_student.tb_student) and role-based dynamic schedule generation.
"""

from typing import List, Tuple, Dict, Any
from chronos.core.types import RuleDef, EventScheduleDef, StructuralDomainModel, EntityRole

class BusinessRuleBuilder:
    """Constructs invariant rules and declarative event decision trees for the domain model."""

    @staticmethod
    def _normalize_name(tname: str) -> str:
        """Extracts table base name from schema-qualified string (e.g., sch_student.tb_student -> tb_student)."""
        return tname.split(".")[-1].lower()

    @staticmethod
    def build_default_rules_and_schedules(sdm: StructuralDomainModel) -> Tuple[List[RuleDef], List[Dict[str, Any]]]:
        rules: List[RuleDef] = []
        schedules: List[Dict[str, Any]] = []

        table_map = {BusinessRuleBuilder._normalize_name(tname): tname for tname in sdm.tables.keys()}

        # 1. Higher Education & Student Domain (matching sch_student, sch_attendance, sch_assessment)
        student_table = table_map.get("tb_student") or table_map.get("tb_student_profile")
        att_table = table_map.get("tb_attendance") or table_map.get("tb_att_log") or table_map.get("tb_att_policy")
        result_table = table_map.get("tb_exam_result") or table_map.get("tb_assessment_result") or table_map.get("tb_validation_result")

        if student_table:
            rules.append(
                RuleDef(
                    name="PlacementEligibilityInvariant",
                    target_entity=student_table,
                    invariant_expr="cgpa >= 7.5 and fee_status == 'CLEAR' and attendance_pct >= 0.75",
                    on_violation_action="SET placement_eligible = True"
                )
            )

        if att_table and student_table:
            schedules.append({
                "name": "DailyAttendanceSchedule",
                "cron": "DAILY_08:00",
                "target_actor": student_table,
                "log_target_entity": att_table,
                "decision_tree": {
                    "condition": "random() < (0.30 + 0.65 * conscientiousness)",
                    "mutation": {
                        "attribute": "attendance_pct",
                        "formula": "round(((attendance_pct * (tick - 1)) + 1.0) / tick, 3)"
                    },
                    "event_payload": {
                        "is_present": "1",
                        "timestamp": "'2026-08-01 08:00:00'"
                    }
                }
            })

        # 2. Banking Domain (matching sch_banking / TB_CUSTOMER)
        cust_table = table_map.get("tb_customer")
        txn_table = table_map.get("tb_transaction_log") or table_map.get("tb_transaction")

        if cust_table:
            rules.append(
                RuleDef(
                    name="LowRiskCreditInvariant",
                    target_entity=cust_table,
                    invariant_expr="credit_score >= 700",
                    on_violation_action="SET risk_status = 'LOW_RISK'"
                )
            )

        if txn_table and cust_table:
            schedules.append({
                "name": "BankingTransactionSchedule",
                "cron": "DAILY_12:00",
                "target_actor": cust_table,
                "log_target_entity": txn_table,
                "decision_tree": {
                    "condition": "random() < 0.40",
                    "mutation": {
                        "attribute": "account_balance",
                        "formula": "round(max(0.0, account_balance + (random_uniform(100, 1500) * (1 if random() < (0.4 + 0.4 * financial_stability) else -1))), 2)"
                    },
                    "event_payload": {
                        "account_id": "'tb_account_' + str(id.split('_')[-1])",
                        "amount": "round(random_uniform(100, 1500), 2)",
                        "txn_type": "'DEPOSIT' if random() < 0.5 else 'WITHDRAWAL'",
                        "timestamp": "'2026-08-01 12:00:00'"
                    }
                }
            })

        # 3. OneApp Enterprise Platform (matching sch_aaa, sch_lms, sch_org, sch_employee, sch_fees)
        user_table = table_map.get("tb_oneapp_user") or table_map.get("tb_user") or table_map.get("tb_emp") or table_map.get("tb_employee")
        activity_table = table_map.get("tb_oneapp_activity_log") or table_map.get("tb_activity_log") or table_map.get("tb_audit_log") or table_map.get("tb_lms_activity_log")
        fee_table = table_map.get("tb_fee_payment") or table_map.get("tb_payment_transaction")

        if user_table:
            rules.append(
                RuleDef(
                    name="ActiveUserStatusInvariant",
                    target_entity=user_table,
                    invariant_expr="conscientiousness >= 0.30",
                    on_violation_action="SET status = 'ACTIVE'"
                )
            )

        if activity_table and user_table:
            schedules.append({
                "name": "UserActivityLogSchedule",
                "cron": "DAILY_10:00",
                "target_actor": user_table,
                "log_target_entity": activity_table,
                "decision_tree": {
                    "condition": "random() < (0.20 + 0.60 * conscientiousness)",
                    "mutation": None,
                    "event_payload": {
                        "user_id": "id",
                        "activity_type": "'DOCUMENT_EDIT' if random() < 0.5 else 'RESOURCE_ACCESS'",
                        "timestamp": "'2026-08-01 10:00:00'"
                    }
                }
            })

        # 4. Universal Fallback Event Schedule Generator for Event Log Tables
        # Assigns dynamic event generation schedules to any table classified as EVENT_LOG if not matched above
        actors = [tname for tname, tdef in sdm.tables.items() if tdef.inferred_role == EntityRole.ACTOR]
        event_logs = [tname for tname, tdef in sdm.tables.items() if tdef.inferred_role == EntityRole.EVENT_LOG]

        if actors and event_logs:
            for idx, log_tbl in enumerate(event_logs[:8]):
                if not any(s.get("log_target_entity") == log_tbl for s in schedules):
                    target_act = actors[idx % len(actors)]
                    schedules.append({
                        "name": f"DynamicEventSchedule_{idx+1}",
                        "cron": "DAILY_12:00",
                        "target_actor": target_act,
                        "log_target_entity": log_tbl,
                        "decision_tree": {
                            "condition": "random() < (0.25 + 0.50 * conscientiousness)",
                            "mutation": None,
                            "event_payload": {
                                "actor_id": "id",
                                "status": "'COMPLETED'",
                                "timestamp": "'2026-08-01 12:00:00'"
                            }
                        }
                    })

        return rules, schedules
