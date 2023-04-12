/** @odoo-module */
import { useService } from "@web/core/utils/hooks";

const { Component, onWillStart } = owl;
const session = require('web.session');

export class TaskDashBoardList extends Component {
    setup() {
        this.orm = useService("orm");
        this.action = useService("action");

        onWillStart(async () => {
            debugger
            this.ccppData = await this.orm.call(
                "account.analytic.line",
                "retrieve_dashboard",
                { context: this.context },
            );
        });
    }

    //async openCreate() {
    //    this._rpc({
    //        model: 'project.project',
     //       method: 'open_create_step',
     //   });//.then(function () {
        //    self.trigger_up('reload');
        //}
    //}


    //async openCreate() {
    //   this._rpc({
    //               model: 'project.project',
    //               method: 'open_create_step',
    //           });
    //}

    /**
     * This method clears the current search query and activates
     * the filters found in `filter_name` attibute from button pressed
     */
    setSearchContext(ev) {
        let filter_name = ev.currentTarget.getAttribute("filter_name");
        let filters = filter_name.split(',');
        let searchItems = this.env.searchModel.getSearchItems((item) => filters.includes(item.name));
        this.env.searchModel.query = [];
        for (const item of searchItems){
            this.env.searchModel.toggleSearchItem(item.id);
        }
    }
}

TaskDashBoardList.template = 'ccpp.TaskDashboardList'
