/** @odoo-module */

import { CalendarFilterPanel } from "@web/views/calendar/filter_panel/calendar_filter_panel";

const { useState, onWillStart } = owl;

let nextId = 1;

export class CCPPCalendarFilterPanel extends CalendarFilterPanel {

    setup(){
        onWillStart(async () => {
            this.employee_id = await this.orm.call(
                "account.analytic.line",
                "get_employee_calendar",
                { context: this.context },
                
            );
            if (this.props.model.data.filterSections.employee_id && this.props.model.data.filterSections.employee_id.filters){
                for (const filter of this.props.model.data.filterSections.employee_id.filters) {
                    if (this.employee_id !== filter.value) {
                        filter.active = false
                    } else {
                        filter.active = true
                    }
                }
                this.props.model.data.records = await this.props.model.loadRecords(this.props.model.data);
            }
        });
        super.setup();
        
    }
}
CCPPCalendarFilterPanel.template = 'ccpp.CalendarFilterPanel';