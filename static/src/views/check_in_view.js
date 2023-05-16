odoo.define('ccpp.check_in_view', function (require) {
    'use strict';

    var delay = require("web.concurrency");
    var AbstractAction = require('web.AbstractAction');
    var ajax = require('web.ajax');
    var core = require('web.core');
    var rpc = require('web.rpc');
    var web_client = require('web.web_client');
    var session = require('web.session');
    var _t = core._t;
    var QWeb = core.qweb;
    var self = this;
    var currency;
    var Check_In_View = AbstractAction.extend({
        template: 'CheckInTemplateMain',
        events: {
            'click .update_check_in': '_update_check_in',
            'click .skip_done': '_skip_done',
            'click .done': '_done',
            'change .input_value': '_input_value',
        },

        init: function(parent, context) {
            
            this._super(parent, context);
            this.upcoming_events = [];
            this.current_lang=[];
            this.login_employee = [];
            this.latitude = [];
            this.longitude = [];
            this.location_name = [];
            this.step = '1';
            this.is_checkin_calendar = false;
        },

        willStart: function(){
            var self = this;
            var latitude;
            var longitude;
            var x;
            var y;
            this.login_employee = {};
            var latitude, longitude = [];
            self.is_checkin_calendar = this.searchModelConfig.context.is_checkin_calendar
            
            var def = self._rpc({
                model: 'account.analytic.line',
                method: 'get_employee',
                //model: 'hr.employee',
                //method: 'search_read',
                //args: [[['id', '=', 2]]],
                args: [this.searchModelConfig.context.active_id],
                //context: context,
            }).then(function(result) {
                self.employee = result.employee;
                self.analytic_line = result.analytic_line;
                self.date = result.date   
            });

            navigator.geolocation.getCurrentPosition(self._getPosition.bind(self))
                
            return Promise.all([def, this._super.apply(this, arguments)]);
            
        },
        
        _getPosition: async function(position) {
            self = this;
            var latitude = position.coords.latitude;
            var longitude = position.coords.longitude;
            if(latitude && longitude){
                this.latitude = latitude
                this.longitude = longitude
                var ctx = [latitude,longitude]
                var def = await self._rpc({
                    model: 'account.analytic.line',
                    method: 'get_location_name',
                    args: ctx,
                    //context: context,
                }).then(function(result) {
                    self.location_name = result.location_name

                });
                this.location_name = self.location_name;

            } else {
                this.latitude = 0
                this.longitude = 0
            }

            

        },

        start: function() {
            var self = this;
            return this._super().then(function() {
                self.render_dashboards();
            });
        },

        render_dashboards: function() {
            var self = this;
            var template = "";
            if( self.step == '1'){
                template = 'CheckInTemplate1';
                self.$('.o_ccpp_check_in1').append(QWeb.render(template, {widget: self}));
            }
            else{
                template = 'CheckInTemplate2';
                self.$('.o_ccpp_check_in2').append(QWeb.render(template, {widget: self}));
            }
            //_.each(templates, function(template) {
            //    self.$('.o_ccpp_check_in1').append(QWeb.render(template, {widget: self}));
            //});
   

        },

        _update_check_in: function(ev){
            var self = this;
            var analytic_line = this.analytic_line.analytic_line_id;
            
            var current_situation = document.getElementById("current_situation").value;
            var next_action = document.getElementById("next_action").value;
            var latitude = this.latitude;
            var longitude = this.longitude;
            var check_class = $(ev.target).getAttributes('class').class
            var ctx = [analytic_line, latitude, longitude, current_situation, next_action, check_class];
            var def0 =  self._rpc({
                model: 'account.analytic.line',
                method: 'update_check_in',
                args: [ctx],
            }).then(function(result) {
                if (result.purchase_history == true){
                    self.step = '2'
                    
                    self.order_lines = result.order_lines;
                    self.borrow_lines = result.borrow_lines;
                    //self.$('.o_ccpp_check_in').append(QWeb.render('CheckInTemplate2', {widget: self}));
                    self.$('.o_ccpp_check_in1').remove();
                    self.$('.o_ccpp_check_in2').append(QWeb.render('CheckInTemplate2', {widget: self}));
                    //self.$('.o_ccpp_check_in') = QWeb.render('CheckInTemplate2', {widget: self})
                }
                else{
                    
                    if (self.is_checkin_calendar == true){
                        self.do_action('ccpp.act_rocker_timesheet_calendar');
                    } else {
                        self.do_action('ccpp.act_rocker_timesheet_tree');
                }
                }
            });

            return $.when(def0);
        },

        _skip_done: function(){
            self = this;
            var ctx;
            var analytic_line = this.analytic_line.analytic_line_id
            var def =  self._rpc({
                model: 'account.analytic.line',
                method: 'skip',
                 args: [analytic_line],
            }).then(function(result) {    
                
                if (self.is_checkin_calendar == true){
                    self.do_action('ccpp.act_rocker_timesheet_calendar');
                } else {
                    self.do_action('ccpp.act_rocker_timesheet_tree');
                }
                }
            );
        },
        
        _done: function(ev){
            var self = this;
            var ctx;
            var analytic_line = this.analytic_line.analytic_line_id
            // var order_list = []
            // var remain_list = []
            // var borrow_list = []
            // var orderborrow_list = []
            // _.each(this.order_lines, function(order_line) {
            //     
            //     var order = "order" + order_line.phlid
            //     var order_dict = {phlid: document.getElementById(order).value}
            //     order_list.append(order_dict)
            //     var remain = "remain" + order_line.phlid
            //     var remain_dict = {phlid: document.getElementById(remain).value}
            //     remain_list.append(remain_dict)
            //     var borrow = "borrow" + order_line.phlid
            //     var borrow_dict = {phlid: document.getElementById(borrow).value}
            //     borrow_list.append(borrow_dict)
            //     var orderborrow = "orderborrow" + order_line.phlid
            //     var oderborrow_dict = {phlid: document.getElementById(orderborrow).value}
            //     orderborrow_list.append(oderborrow_dict)
            // });
            // ctx = [order_list,remain_list,borrow_list,orderborrow_list]
            var def =  self._rpc({
                model: 'account.analytic.line',
                method: 'done',
                args: [analytic_line],
            }).then(function(result) {    
                
                if (self.is_checkin_calendar == true){
                    self.do_action('ccpp.act_rocker_timesheet_calendar');
                } else {
                    self.do_action('ccpp.act_rocker_timesheet_tree');
            }
                }
            );

        },

        _input_value: function(ev){
            var self = this;
            var phlid;
            var ctx;
            var val;
            var type;
            var task;
            
            phlid = $(ev.target).attr('data-id')
            val = $(ev.target).val()
            type = $(ev.target).getAttributes('class').class
            task = this.analytic_line.analytic_line_id;
            var def =  self._rpc({
                model: 'account.analytic.line',
                method: 'input_value',
                args: [phlid,val,type,task],
            })

        },

        _getPositionError: function (error) {
            console.log("ERROR(" + error.code + "): " + error.message);
            this.latitude = 0
            this.longitude = 0
        },
    });

    core.action_registry.add('check_in_view', Check_In_View);
    return Check_In_View;
});