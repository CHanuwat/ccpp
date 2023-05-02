/** @odoo-module */
import { useService } from "@web/core/utils/hooks";

const { Component, onWillStart } = owl;
const session = require('web.session');

export class CCPPExternalDashBoardListManager extends Component {
    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        

        onWillStart(async () => {
            debugger
            this.externalData = await this.orm.call(
                "ccpp.customer.information",
                "retrieve_dashboard_external",
                { context: this.context },
            );
        });
    }

    async _setMyCustomer(ev){
        const action = await this.orm.call('ccpp.customer.information', 'set_my_customer_external');
        this.action.doAction(action);
    }

    async _setAllCustomer(ev) {
        const action = await this.orm.call('ccpp.customer.information', 'set_all_customer_external');
        this.action.doAction(action);
    }
}

CCPPExternalDashBoardListManager.template = 'ccpp.CCPPExternalDashboardListManager'
