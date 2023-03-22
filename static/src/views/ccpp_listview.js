/** @odoo-module **/

import { registry } from "@web/core/registry";
import { listView } from "@web/views/list/list_view";
import { ListRenderer } from "@web/views/list/list_renderer";
import { CCPPDashBoardList } from '@ccpp/views/ccpp_dashboard_list';

export class CCPPDashBoardListRenderer extends ListRenderer {};

CCPPDashBoardListRenderer.template = 'ccpp.CCPPListView';
CCPPDashBoardListRenderer.components= Object.assign({}, ListRenderer.components, {CCPPDashBoardList})

export const CCPPDashBoardListView = {
    ...listView,
    Renderer: CCPPDashBoardListRenderer,
};

registry.category("views").add("ccpp_dashboard_list", CCPPDashBoardListView);
