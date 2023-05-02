/** @odoo-module **/

import { registry } from "@web/core/registry";
import { listView } from "@web/views/list/list_view";
import { ListRenderer } from "@web/views/list/list_renderer";
import { CCPPExternalDashBoardListManager } from '@ccpp/views/ccpp_external_dashboard_list_manager';

export class CCPPExternalDashBoardListRendererManager extends ListRenderer {};

CCPPExternalDashBoardListRendererManager.template = 'ccpp.CCPPExternalListViewManager';
CCPPExternalDashBoardListRendererManager.components= Object.assign({}, ListRenderer.components, {CCPPExternalDashBoardListManager})

export const CCPPExternalDashBoardListViewManager = {
    ...listView,
    Renderer: CCPPExternalDashBoardListRendererManager,
};

registry.category("views").add("ccpp_external_dashboard_list_manager", CCPPExternalDashBoardListViewManager);
