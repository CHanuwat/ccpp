/** @odoo-module **/

import { CalendarCommonRenderer } from "@web/views/calendar/calendar_common/calendar_common_renderer";
import { CCPPCalendarCommonPopover } from "@ccpp/views/check_in_calendar_common_view";

export class CCPPCalendarCommonRenderer extends CalendarCommonRenderer {}

CCPPCalendarCommonRenderer.components = {
    ...CalendarCommonRenderer.components,
    Popover: CCPPCalendarCommonPopover,
};
