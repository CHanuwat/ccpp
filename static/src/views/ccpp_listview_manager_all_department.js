/** @odoo-module **/

import { registry } from "@web/core/registry";
import { listView } from "@web/views/list/list_view";
import { ListRenderer } from "@web/views/list/list_renderer";
import { CCPPDashBoardListManagerAllDepartment } from '@ccpp/views/ccpp_dashboard_list_manager_all_department';

export class CCPPDashBoardListRendererManagerAllDepartment extends ListRenderer {};

CCPPDashBoardListRendererManagerAllDepartment.template = 'ccpp.CCPPListViewManagerAllDepartment';
CCPPDashBoardListRendererManagerAllDepartment.components= Object.assign({}, ListRenderer.components, {CCPPDashBoardListManagerAllDepartment})

export const CCPPDashBoardListViewManagerAllDepartment = {
    ...listView,
    Renderer: CCPPDashBoardListRendererManagerAllDepartment,
    /*buttonTemplate: "create_test",*/
    /*Controller: TreeButton,*/
};

registry.category("views").add("ccpp_dashboard_list_manager_all_department", CCPPDashBoardListViewManagerAllDepartment);
