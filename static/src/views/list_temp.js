/** @odoo-module **/
import { listView } from "@web/views/list/list_view";
import { ListController } from "@web/views/list/list_controller";
import { registry } from "@web/core/registry";

export const CreateTestIconListView = {
   ...listView,
   buttonTemplate: "create_test",
};

registry.category("views").add("button_create_test", CreateTestIconListView);