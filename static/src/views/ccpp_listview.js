/** @odoo-module **/

import { registry } from "@web/core/registry";
import { listView } from "@web/views/list/list_view";
import { ListRenderer } from "@web/views/list/list_renderer";
import { CCPPDashBoardList } from '@ccpp/views/ccpp_dashboard_list';
import { ListController } from "@web/views/list/list_controller";
import { useService } from '@web/core/utils/hooks';

export class CCPPDashBoardListRenderer extends ListRenderer {};

CCPPDashBoardListRenderer.template = 'ccpp.CCPPListView';
CCPPDashBoardListRenderer.components= Object.assign({}, ListRenderer.components, {CCPPDashBoardList})

export class CCPPListController extends ListController {


    setup() {
        super.setup();
        this.orm = useService('orm');
        this.actionService = useService('action');
        this.rpc = useService("rpc");
        this.user = useService("user");
    }

    // button create step
    async openCreate() {
        const action = await this.orm.call('project.project', 'open_create_step');
        this.actionService.doAction(action);
    }

    // action on click tree
    async openRecord(record) {
        const action = await this.orm.call('project.project', 'check_view_step', [record.resId]);
        this.actionService.doAction(action);
    }

}



export const CCPPDashBoardListView = {
    ...listView,
    Renderer: CCPPDashBoardListRenderer,
    buttonTemplate: "create_test",
    Controller: CCPPListController,
};

registry.category("views").add("ccpp_dashboard_list", CCPPDashBoardListView);
