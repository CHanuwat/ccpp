/** @odoo-module **/

import { CalendarController } from "@web/views/calendar/calendar_controller";
import { CCPPCalendarFilterPanel } from "@ccpp/views/check_in_calendar_filter_panel";

export class CCPPCalendarController extends CalendarController {}

CCPPCalendarController.template = "ccpp.CalendarController";
CCPPCalendarController.components = {
    ...CCPPCalendarController.components,
    FilterPanel: CCPPCalendarFilterPanel,
}
