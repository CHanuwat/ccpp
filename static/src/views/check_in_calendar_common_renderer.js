/** @odoo-module **/

import { CalendarCommonRenderer } from "@web/views/calendar/calendar_common/calendar_common_renderer";
import { CCPPCalendarCommonPopover } from "@ccpp/views/check_in_calendar_common_view";

export class CCPPCalendarCommonRenderer extends CalendarCommonRenderer {

    onEventRender(info) {
        super.onEventRender(...arguments);
        const { el, event } = info;
        const record = this.props.model.records[event.id];
        el.classList.remove('o_calendar_color_6');
        el.classList.remove('o_calendar_color_11');
        if (record.rawRecord.state == 'open'){
            el.classList.add("o_calendar_color_6");

        }
        if (record.rawRecord.state == 'done'){
            el.classList.add("o_calendar_color_11");
        }
        debugger
        
    }
}

CCPPCalendarCommonRenderer.components = {
    ...CalendarCommonRenderer.components,
    Popover: CCPPCalendarCommonPopover,
};
