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

    async openCreate() {
        const action = await this.orm.call('project.project', 'open_create_step');
        this.actionService.doAction(action);
    }
}

/*var TreeButton = ListController.extend({
    button_template: 'ccpp.buttons',
    xmlDependencies: ['/ccpp/static/src/xml/tree_button.xml'],
    events: _.extend({}, ListController.prototype.events, {
        'click .open_create_ccpp': '_OpenWizard',
    }),
    _OpenWizard: function () {
        var self = this;
         this.do_action({
            type: 'ir.actions.act_window',
            res_model: 'ccpp.purchase.history.line',
            name :'Open Wizard',
            view_mode: 'form',
            view_type: 'form',
            views: [[false, 'form']],
            target: 'new',
            res_id: false,
        });
    }
 });*/

export const CCPPDashBoardListView = {
    ...listView,
    Renderer: CCPPDashBoardListRenderer,
    buttonTemplate: "create_test",
    Controller: CCPPListController,
};

registry.category("views").add("ccpp_dashboard_list", CCPPDashBoardListView);
