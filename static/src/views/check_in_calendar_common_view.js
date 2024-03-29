/** @odoo-module **/
'use strict';
import { CalendarCommonPopover } from "@web/views/calendar/calendar_common/calendar_common_popover";
import { useService } from "@web/core/utils/hooks";
const { Component, onWillStart } = owl

export class CCPPCalendarCommonPopover extends CalendarCommonPopover {
    setup() {
        super.setup();

        this.orm = useService("orm");
        this.action = useService("action");



        var self = this;

        onWillStart(async () => {
            this.job_current_ids = await this.orm.call(
                "account.analytic.line",
                "check_job_current",
                //[this.props.record.resId], // self
            );
        });
    }

    openCheckIn() {
        var context = {};
        context['active_id'] = this.props.record.id;
        context['is_checkin_calendar'] = true;
        this.action.doAction('ccpp.action_check_in',{
            additionalContext: context,
        });
        this.props.close();
    }

    openSituation() {
        var context = {};
        context['active_id'] = this.props.record.id;
        context['res_id'] = this.props.record.id;

        // context['is_checkin_calendar'] = true;
        this.action.doAction({type: 'ir.actions.act_window',
            res_model: 'account.analytic.line',
            res_id: this.props.record.id,
            views: [[false, 'form']],});
        this.props.close();
    }

    async cancelSituation() {
        var context = {};
        context['active_id'] = this.props.record.id;
        context['res_id'] = this.props.record.id;
        var self = this;
        debugger
        
        var def =  await this.orm.call(
            'account.analytic.line',
            'cancel_task',
            [this.props.record.id],
        ).then(function(result) {    
            
            this.action.doAction({type: 'ir.actions.act_window',
            res_model: 'account.analytic.line',
            res_id: this.props.record.id,
            views: [[false, 'form']],});
            }
        );
        
        this.props.close();
    }

    get isNotDone() {
        const state = this.props.record.rawRecord.state;
        if (state == 'done'){
            return false
        } else {
            return true
        }
    }

    get isOwner() {
        if (this.job_current_ids.includes(this.props.record.rawRecord.job_id[0])){
            return true
        } else {
            return false
        }
        
        
    }
}

CCPPCalendarCommonPopover.subTemplates = {
    ...CalendarCommonPopover.subTemplates,
    footer: "check_in_calendar",
};
