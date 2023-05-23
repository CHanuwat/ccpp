/** @odoo-module */

import { CalendarFilterPanel } from "@web/views/calendar/filter_panel/calendar_filter_panel";

const { useState, onWillStart } = owl;

let nextId = 1;

export class CCPPCalendarFilterPanel extends CalendarFilterPanel {


    getAutoCompleteProps(section) {
        return {
            autoSelect: true,
            resetOnSelect: true,
            placeholder: `+ ${_t("Add")} ${section.label}`,
            sources: [
                {
                    placeholder: _t("Loading..."),
                    options: (request) => this.loadSource(section, request),
                },
            ],
            onSelect: (option, params = {}) => {
                if (option.action) {
                    option.action(params);
                    return;
                }
                this.props.model.createFilter(section.fieldName, option.value);
            },
            value: "",
        };
    }

    async loadSource(section, request) {
        const resModel = this.props.model.fields[section.fieldName].relation;
        const domain = [
            ["id", "not in", section.filters.filter((f) => f.type !== "all").map((f) => f.value)],
        ];
        const records = await this.orm.call(resModel, "name_search", [], {
            name: request,
            operator: "ilike",
            args: domain,
            limit: 8,
            context: {},
        });

        const options = records.map((result) => ({
            value: result[0],
            label: result[1],
        }));

        if (records.length > 7) {
            options.push({
                label: _t("Search More..."),
                action: () => this.onSearchMore(section, resModel, domain, request),
            });
        }

        if (records.length === 0) {
            options.push({
                label: _t("No records"),
                classList: "o_m2o_no_result",
                unselectable: true,
            });
        }

        return options;
    }

    async onSearchMore(section, resModel, domain, request) {
        debugger
        const dynamicFilters = [];
        if (request.length) {
            const nameGets = await this.orm.call(resModel, "name_search", [], {
                name: request,
                args: domain,
                operator: "ilike",
                context: {},
            });
            dynamicFilters.push({
                description: sprintf(_t("Quick search: %s"), request),
                domain: [["id", "in", nameGets.map((nameGet) => nameGet[0])]],
            });
        }
        const title = sprintf(_t("Search: %s"), section.label);
        this.addDialog(SelectCreateDialog, {
            title,
            noCreate: true,
            multiSelect: false,
            resModel,
            context: {},
            domain,
            onSelected: ([resId]) => this.props.model.createFilter(section.fieldName, resId),
            dynamicFilters,
        });
    }

    get nextFilterId() {
        debugger
        nextId += 1;
        return nextId;
    }

    isAllActive(section) {
        debugger
        let active = true;
        for (const filter of section.filters) {
            if (filter.type !== "all" && !filter.active) {
                active = false;
                break;
            }
        }
        return active;
    }
    getFilterTypePriority(type) {
        debugger
        return ["user", "record", "dynamic", "all"].indexOf(type);
    }
    getSortedFilters(section) {
        debugger
        return section.filters.slice().sort((a, b) => {
            if (a.type === b.type) {
                const va = a.value ? -1 : 0;
                const vb = b.value ? -1 : 0;
                if (a.type === "dynamic" && va !== vb) {
                    return va - vb;
                }
                return b.label.localeCompare(a.label);
            } else {
                return this.getFilterTypePriority(a.type) - this.getFilterTypePriority(b.type);
            }
        });
    }

    toggleSection(section) {
        debugger
        if (section.canCollapse) {
            this.state.collapsed[section.fieldName] = !this.state.collapsed[section.fieldName];
        }
    }

    isSectionCollapsed(section) {
        debugger
        return this.state.collapsed[section.fieldName] || false;
    }

    closeTooltip() {
        debugger
        if (this.removePopover) {
            this.removePopover();
            this.removePopover = null;
        }
    }

    onFilterInputChange(section, filter, ev) {
        debugger
        this.props.model.updateFilters(section.fieldName, {
            [filter.value]: ev.target.checked,
        });
    }

    onAllFilterInputChange(section, ev) {
        debugger
        const filters = {};
        for (const filter of section.filters) {
            if (filter.type !== "all") {
                filters[filter.value] = ev.target.checked;
            }
        }
        this.props.model.updateFilters(section.fieldName, filters);
    }

    onFilterMouseEnter(section, filter, ev) {
        debugger
        this.closeTooltip();
        if (!section.hasAvatar || !filter.hasAvatar) {
            return;
        }

        this.removePopover = this.popover.add(
            ev.currentTarget,
            CalendarFilterTooltip,
            { section, filter },
            {
                closeOnClickAway: false,
                popoverClass: "o-calendar-filter--tooltip",
                position: "top",
            }
        );
    }

    onFilterMouseLeave() {
        debugger
        this.closeTooltip();
    }

    onFilterRemoveBtnClick(section, filter) {
        debugger
        this.props.model.unlinkFilter(section.fieldName, filter.recordId);
    }

    onFieldChanged(fieldName, filterValue) {
        debugger
        this.state.fieldRev += 1;
        this.props.model.createFilter(fieldName, filterValue);
    }
}
CCPPCalendarFilterPanel.template = 'ccpp.CalendarFilterPanel';