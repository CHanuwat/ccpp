/** @odoo-module **/

import { registry } from "@web/core/registry";
import { listView } from "@web/views/list/list_view";
import { ListRenderer } from "@web/views/list/list_renderer";
import { CCPPDashBoardListManager } from '@ccpp/views/ccpp_dashboard_list_manager';

export class CCPPDashBoardListRendererManager extends ListRenderer {};

CCPPDashBoardListRendererManager.template = 'ccpp.CCPPListViewManager';
CCPPDashBoardListRendererManager.components= Object.assign({}, ListRenderer.components, {CCPPDashBoardListManager})

export const CCPPDashBoardListViewManager = {
    ...listView,
    Renderer: CCPPDashBoardListRendererManager,
};

registry.category("views").add("ccpp_dashboard_list_manager", CCPPDashBoardListViewManager);
