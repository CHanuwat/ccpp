/** @odoo-module **/

import { CalendarModel } from "@web/views/calendar/calendar_model";

export class CCPPCalendarModel extends CalendarModel {
    async updateFiltersNew(fieldName, filters) {
        const section = this.data.filterSections[fieldName];
        if (section) {
            for (const value in filters) {
                const active = filters[value];
                const filter = section.filters.find((filter) => `${filter.value}` === value);
                if (filter) {
                    filter.active = active;
                    const info = this.meta.filtersInfo[fieldName];
                    if (
                        filter.recordId &&
                        info &&
                        info.writeFieldName &&
                        info.writeResModel &&
                        info.filterFieldName
                    ) {
                        const data = {
                            [info.filterFieldName]: active,
                        };
                        debugger
                        await this.orm.write(info.writeResModel, [filter.recordId], data);
                    }
                }
            }
        }
        debugger
        this.update_filters = false
        //await this.load();
    }
    
}

