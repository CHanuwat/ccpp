/** @odoo-module **/

import { CalendarCommonPopover } from "@web/views/calendar/calendar_common/calendar_common_popover";
import { useService } from "@web/core/utils/hooks";

export class CCPPCalendarCommonPopover extends CalendarCommonPopover {
    setup() {
        super.setup();

        this.action = useService("action");
    }

    openCheckIn() {
        var context = {};
        debugger
        context['active_id'] = this.props.record.id;
        this.action.doAction('ccpp.action_check_in',{
            additionalContext: context,
        });
    }

    get isNotDone() {
        const state = this.props.record.rawRecord.state;
        debugger
        if (state == 'done'){
            return false
        } else {
            return true
        }
    }
}

CCPPCalendarCommonPopover.subTemplates = {
    ...CalendarCommonPopover.subTemplates,
    footer: "check_in_calendar",
};
