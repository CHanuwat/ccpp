/** @odoo-module **/

import { CalendarRenderer } from "@web/views/calendar/calendar_renderer";
import { CCPPCalendarCommonRenderer } from "@ccpp/views/check_in_calendar_common_renderer";
import { AttendeeCalendarYearRenderer } from "@calendar/views/attendee_calendar/year/attendee_calendar_year_renderer";

export class CCPPCalendarRenderer extends CalendarRenderer {}
CCPPCalendarRenderer.components = {
    ...CalendarRenderer.components,
    day: CCPPCalendarCommonRenderer,
    week: CCPPCalendarCommonRenderer,
    month: CCPPCalendarCommonRenderer,
    //year: AttendeeCalendarYearRenderer,
};
