/** @odoo-module */
import { useService } from "@web/core/utils/hooks";

const { Component, onWillStart } = owl;
const session = require('web.session');

export class CCPPInternalDashBoardListManager extends Component {
    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        

        onWillStart(async () => {
            debugger
            this.internalData = await this.orm.call(
                "ccpp.customer.information",
                "retrieve_dashboard_internal",
                { context: this.context },
            );
        });
    }

    setSearchContext(ev) {
        let filter_name = ev.currentTarget.getAttribute("filter_name");
        let filters = filter_name.split(',');
        let searchItems = this.env.searchModel.getSearchItems((item) => filters.includes(item.name));
        this.env.searchModel.query = [];
        for (const item of searchItems){
            this.env.searchModel.toggleSearchItem(item.id);
        }
    }

    async _setMyCustomer(ev){
        const action = await this.orm.call('ccpp.customer.information', 'set_my_customer_internal');
        this.action.doAction(action);
    }

    async _setAllCustomer(ev) {
        const action = await this.orm.call('ccpp.customer.information', 'set_all_customer_internal');
        this.action.doAction(action);
    }
}

CCPPInternalDashBoardListManager.template = 'ccpp.CCPPInternalDashboardListManager'
