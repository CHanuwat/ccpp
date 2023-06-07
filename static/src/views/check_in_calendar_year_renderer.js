/** @odoo-module **/

import { CalendarYearRenderer } from "@web/views/calendar/calendar_year/calendar_year_renderer";
import { CCPPCalendarYearPopover } from "@ccpp/views/check_in_calendar_year_popover";

export class CCPPCalendarYearRenderer extends CalendarYearRenderer {
    
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
        
}
}

CCPPCalendarYearRenderer.components = {
    ...CalendarYearRenderer,
    Popover: CCPPCalendarYearPopover,
};

