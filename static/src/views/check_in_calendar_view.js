/** @odoo-module **/

import { registry } from "@web/core/registry";
import { calendarView } from "@web/views/calendar/calendar_view";
import { CCPPCalendarController } from "@ccpp/views/check_in_calendar_controller";
import { CCPPCalendarModel } from "@ccpp/views/check_in_calendar_model";
import { CCPPCalendarRenderer } from "@ccpp/views/check_in_calendar_renderer";

export const CCPPCalendarView = {
    ...calendarView,
    Renderer: CCPPCalendarRenderer,
    Controller: CCPPCalendarController,
    Model: CCPPCalendarModel,
};

registry.category("views").add("ccpp_calendar", CCPPCalendarView);
