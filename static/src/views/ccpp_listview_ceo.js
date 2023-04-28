/** @odoo-module **/

import { registry } from "@web/core/registry";
import { listView } from "@web/views/list/list_view";
import { ListRenderer } from "@web/views/list/list_renderer";
import { CCPPDashBoardListCeo } from '@ccpp/views/ccpp_dashboard_list_ceo';


export class CCPPDashBoardListRendererCeo extends ListRenderer {};

CCPPDashBoardListRendererCeo.template = 'ccpp.CCPPListViewCeo';
CCPPDashBoardListRendererCeo.components= Object.assign({}, ListRenderer.components, {CCPPDashBoardListCeo})

// export class CCPPDashBoardControllerCeo extends ListController {

//     setup() {
//         super.setup();
//         this.orm = useService('orm');
//     }

//     async openRecord(record) {
//         const action = await this.orm.call('project.project', 'check_view_step', [record.resId]);
//         this.actionService.doAction(action);
//     }

// }

export const CCPPDashBoardListViewCeo = {
    ...listView,
    Renderer: CCPPDashBoardListRendererCeo,
    /*buttonTemplate: "create_test",*/
    // Controller: CCPPDashBoardControllerCeo
};

registry.category("views").add("ccpp_dashboard_list_ceo", CCPPDashBoardListViewCeo);
