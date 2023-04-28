// example for renderer or controller only

odoo.define('ccpp.ccpp_list_view_action', function (require) {
    'use strict';

    var ListRenderer = require('web.ListRenderer');
    var view_registry = require('web.view_registry');

    var MyListView = ListRenderer.extend({

        _onRowClicked: function (event) {
            // Call the parent method first to preserve existing behavior
            debugger
            this._super(event);

            // Add your custom behavior here
            
            

            // For example, you could display a popup dialog
            // when a certain type of record is clicked
        },
    });

    view_registry.add('ccpp_list_view_action', MyListView);

    return MyListView;
});