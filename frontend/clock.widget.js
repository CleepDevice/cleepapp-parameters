/**
 * Clock widget
 * Display clock dashboard widget
 */
angular
.module('Cleep')
.directive('clockWidget', ['$filter',
function($filter) {

    var widgetClockController = ['$scope', function($scope) {
        var self = this;
        self.device = $scope.device;
        self.device.widget = {
            colspan: 1,
            rowspan: 1,
        };
        self.footer = [];

        self.$onInit = function() {
            self.footer.push({
                icon: 'weather-sunset-up',
                tooltip: 'Sunrise',
                label: $filter('hrTime')(self.device.sunrise),
            });
            self.footer.push({
                icon: 'weather-sunset-down',
                tooltip: 'Sunset',
                label: $filter('hrTime')(self.device.sunset),
            });
        };

    }];

    return {
        restrict: 'EA',
        templateUrl: 'clock.widget.html',
        scope: {
            device: '=',
            conf: '<',
        },
        controller: widgetClockController,
        controllerAs: 'widgetCtl'
    };
}]);

