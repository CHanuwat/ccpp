/** @odoo-module **/

import { registry } from "@web/core/registry";
import { listView } from "@web/views/list/list_view";
import { ListRenderer } from "@web/views/list/list_renderer";
import { CCPPInternalDashBoardListManager } from '@ccpp/views/ccpp_internal_dashboard_list_manager';

export class CCPPInternalDashBoardListRendererManager extends ListRenderer {};

CCPPInternalDashBoardListRendererManager.template = 'ccpp.CCPPInternalListViewManager';
CCPPInternalDashBoardListRendererManager.components= Object.assign({}, ListRenderer.components, {CCPPInternalDashBoardListManager})

export const CCPPInternalDashBoardListViewManager = {
    ...listView,
    Renderer: CCPPInternalDashBoardListRendererManager,
};

registry.category("views").add("ccpp_internal_dashboard_list_manager", CCPPInternalDashBoardListViewManager);
