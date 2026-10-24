import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi import HTTPException
from pydantic import ValidationError

backend_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(backend_dir))

if "hangarkit.integrations" not in sys.modules:
    integrations = types.ModuleType("hangarkit.integrations")
    integrations.order_admin = types.SimpleNamespace(ensure_access=lambda **kwargs: None, call=lambda *args, **kwargs: None)
    sys.modules["hangarkit.integrations"] = integrations

from routers.order_admin import OrderSearch, Target, check_access, search_orders
from routers import order_admin as route


class OrderAdminAccessTests(unittest.TestCase):
    def test_target_accepts_selected_environment_and_region(self):
        target = Target(env="test", region="sg")
        with patch.object(route.order_admin, "ensure_access", return_value={"state": "ready"}) as ensure:
            self.assertEqual(check_access(target), {"state": "ready"})
        ensure.assert_called_once_with(env="test", region="sg")

    def test_target_rejects_invalid_values(self):
        for values in ({"env": "https://example.com", "region": "sg"}, {"env": "test", "region": "../sg"}):
            with self.subTest(values=values), self.assertRaises(ValidationError):
                Target(**values)

    def test_provider_failure_has_safe_retry_message(self):
        with patch.object(route.order_admin, "ensure_access", side_effect=RuntimeError("secret upstream detail")):
            with self.assertRaises(HTTPException) as raised:
                check_access(Target(env="test", region="sg"))
        self.assertEqual(raised.exception.status_code, 503)
        self.assertNotIn("secret", raised.exception.detail)

    def test_search_uses_cataloged_operation_and_numeric_id_fallback(self):
        empty = {"success": True, "result": {"order_list": [], "has_more": False}}
        matched = {"success": True, "result": {"order_list": [{"order_id": 42, "order_sn": "42", "buyer_name": "buyer"}], "has_more": False}}
        with patch.object(route.order_admin, "call", side_effect=[empty, matched]) as call:
            result = search_orders(OrderSearch(env="test", region="sg", order_key="42"))
        self.assertEqual(result["orders"][0]["order_sn"], "42")
        self.assertEqual(call.call_count, 2)
        self.assertEqual(call.call_args_list[0].args, ("query-order-list-with-filters",))
        self.assertEqual(call.call_args_list[0].kwargs["json"], {"limit": 20, "offset": 0, "order_id": 42})
        self.assertEqual(call.call_args_list[1].kwargs["json"], {"limit": 20, "offset": 0, "order_sn": "42"})

    def test_search_filters_and_pagination(self):
        response = {"order_list": [{"order_id": 8, "payment_method": "card", "fulfilment_channel": {"id": 2, "name": "Doorstep"}}], "has_more": True}
        with patch.object(route.order_admin, "call", return_value=response) as call:
            result = search_orders(OrderSearch(
                env="test", region="sg", buyer_name=" buyer ", payment_method=1, offset=20
            ))
        self.assertEqual(result["offset"], 20)
        self.assertTrue(result["has_more"])
        self.assertEqual(result["orders"][0]["fulfilment_channel"]["id"], 2)
        self.assertEqual(result["orders"][0]["order_id"], "8")
        self.assertEqual(call.call_args.kwargs["json"], {
            "limit": 20, "offset": 20, "buyer_name": "buyer", "payment_method": 1
        })

    def test_blank_search_browses_latest_orders(self):
        with patch.object(route.order_admin, "call", return_value={"order_list": [{"order_id": 12}], "has_more": True}) as call:
            result = search_orders(OrderSearch(env="test", region="sg"))
        self.assertEqual(call.call_args.kwargs["json"], {"limit": 20, "offset": 0})
        self.assertEqual(result["orders"][0]["order_id"], "12")
        self.assertTrue(result["has_more"])

    def test_cross_border_and_date_ranges(self):
        with patch.object(route.order_admin, "call", return_value={"order_list": [], "has_more": False}) as call:
            search_orders(OrderSearch(
                env="test", region="sg", cross_border=False,
                ctime_gte=1700000000, ctime_lte=1700086399,
                mtime_gte=1700000000, mtime_lte=1700086399,
            ))
        self.assertEqual(call.call_args.kwargs["json"], {
            "limit": 20, "offset": 0, "cross_border": False,
            "ctime_gte": 1700000000, "ctime_lte": 1700086399,
            "mtime_gte": 1700000000, "mtime_lte": 1700086399,
        })
        with self.assertRaises(ValidationError):
            OrderSearch(env="test", region="sg", ctime_gte=20, ctime_lte=10)

    def test_search_hides_upstream_failure(self):
        with patch.object(route.order_admin, "call", return_value={"result": {"error_msg": "private error", "order_list": []}}):
            with self.assertRaises(HTTPException) as raised:
                search_orders(OrderSearch(env="test", region="sg", order_key="ABC"))
        self.assertEqual(raised.exception.status_code, 502)
        self.assertNotIn("private", raised.exception.detail)

    def test_large_order_ids_remain_exact_strings_in_browser_response(self):
        response = {"order_list": [{"order_id": 9007199254740993, "checkout_id": 9007199254740995}]}
        with patch.object(route.order_admin, "call", return_value=response):
            result = search_orders(OrderSearch(env="test", region="sg", order_key="ABC"))
        self.assertEqual(result["orders"][0]["order_id"], "9007199254740993")
        self.assertEqual(result["orders"][0]["checkout_id"], "9007199254740995")

    def test_empty_proto_response_can_omit_order_list(self):
        with patch.object(route.order_admin, "call", return_value={"has_more": False}):
            result = search_orders(OrderSearch(env="test", region="sg", order_key="ABC"))
        self.assertEqual(result, {"orders": [], "has_more": False, "offset": 0, "limit": 20})


if __name__ == "__main__":
    unittest.main()
