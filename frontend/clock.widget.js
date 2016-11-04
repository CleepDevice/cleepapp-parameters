/**
 * Clock widget
 * Display clock dashboard widget
 */
angular
.module('Cleep')
.directive('clockWidget', ['parametersService',
function(parametersService) {

    var widgetClockController = ['$scope', function($scope) {
        var self = this;
        self.device = $scope.device;
    }];

    return {
        restrict: 'EA',
        templateUrl: 'clock.widget.html',
        replace: true,
        scope: {
            'device': '='
        },
        controller: widgetClockController,
        controllerAs: 'widgetCtl'
    };
}]);

