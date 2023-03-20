/** @odoo-module **/

import { useService } from "@web/core/utils/hooks";
import { registry } from "@web/core/registry";
import { FormController } from "@web/views/form/form_controller";
import { formView } from "@web/views/form/form_view";

import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";

export class CCPPLocationController extends FormController {
    setup() {
        super.setup();
    }

    async get_location() {
        debugger
        var self = this;
            var options = {
                enableHighAccuracy: true,
                timeout: 5000,
                maximumAge: 60000,
            };
            if (navigator.geolocation) {
                navigator.geolocation.getCurrentPosition(
                    self._get_location.bind(self),
                    options
                );
            }

    }

    async _get_location() {
        debugger
        var self = this;
        const ctx = Object.assign(session.user_context, {
            latitude: position.coords.latitude,
            longitude: position.coords.longitude,
        });
        this._rpc({
            model: "project.update",
            method: "get_location",
            args: [
                
            ],
            context: ctx,
        }).then(function (result) {
            if (result.action) {
                self.do_action(result.action);
            } else if (result.warning) {
                self.do_warn(result.warning);
            }
        });
    }
    
    };


export const CCPPLocationFormView = {
    ...formView,
    Controller: CCPPLocationController,
};

registry.category("views").add("ccpp_location", CCPPLocationFormView);
