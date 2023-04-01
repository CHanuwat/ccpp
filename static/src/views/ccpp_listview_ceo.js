/** @odoo-module **/

import { registry } from "@web/core/registry";
import { listView } from "@web/views/list/list_view";
import { ListRenderer } from "@web/views/list/list_renderer";
import { CCPPDashBoardListCeo } from '@ccpp/views/ccpp_dashboard_list_ceo';

export class CCPPDashBoardListRendererCeo extends ListRenderer {};

CCPPDashBoardListRendererCeo.template = 'ccpp.CCPPListViewCeo';
CCPPDashBoardListRendererCeo.components= Object.assign({}, ListRenderer.components, {CCPPDashBoardListCeo})

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

export const CCPPDashBoardListViewCeo = {
    ...listView,
    Renderer: CCPPDashBoardListRendererCeo,
    /*buttonTemplate: "create_test",*/
    /*Controller: TreeButton,*/
};

registry.category("views").add("ccpp_dashboard_list_ceo", CCPPDashBoardListViewCeo);
