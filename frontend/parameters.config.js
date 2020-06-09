/**
 * Parameters config directive
 * Handle parameters configuration
 */
var parametersConfigDirective = function(toast, parametersService, cleepService, $timeout) {

    var parametersController = ['$scope', function($scope)
    {
        var self = this;
        self.tabIndex = 'hostname';
        self.sunset = null;
        self.sunrise = null;
        self.hostname = '';
        self.hostnamePattern = '^[a-zA-Z][0-9a-zA-Z\-]{3,}[^-]$';
        self.position = {
            latitude: 0,
            longitude: 0
        };
        self.sun = {
            sunrise: 0,
            sunset: 0
        };
        self.country = {
            country: null,
            alpha2: null
        };
        self.timezone = null;

        /**
         * Set hostname
         */
        self.setHostname = function()
        {
            parametersService.setHostname(self.hostname)
                .then(function(resp) {
                    return cleepService.reloadModuleConfig('parameters');
                })
                .then(function(config) {
                    self.updateConfig(config);
                    toast.success('Device name saved');
                });
        };

        /**
         * Set position
         */
        self.setPosition = function()
        {
            //check values
            if( !$scope.cleepposition || !$scope.cleepposition.lat || !$scope.cleepposition.lng ) {
                toast.info('Please select position before setting position');
                return;
            }
            if( $scope.cleepposition.lat==self.position.latitude && $scope.cleepposition.lng==self.position.longitude ) {
                toast.info('Position not changed');
                return;
            }

            toast.loading('Setting localisation...');
            parametersService.setPosition($scope.cleepposition.lat, $scope.cleepposition.lng)
                .then(function(resp) {
                    return cleepService.reloadModuleConfig('parameters');
                })
                .then(function(config) {
                    self.updateConfig(config);
                    toast.success('Localisation saved');
                });
        };

        /**
         * Update controller config
         */
        self.updateConfig = function(config)
        {
            self.position = config.position;
            self.hostname = config.hostname;
            self.sun = config.sun;
            self.country = config.country;
            self.timezone = config.timezone;
        };

        /**
         * Init controller
         */
        self.init = function()
        {
            cleepService.getModuleConfig('parameters')
                .then(function(config) {
                    //update config
                    self.updateConfig(config);

                    //init leaflet
                    angular.extend($scope, {
                        cleepposition: {
                            lat: self.position.latitude,
                            lng: self.position.longitude,
                            zoom: 8
                        },
                        cleepdefaults: {
                            scrollWheelZoom: false,
                            minZoom: 5,
                            maxZoom: 12
                        }
                    });
                });
        };
    }];

    var parametersLink = function(scope, element, attrs, controller) {
        controller.init();
    };

    return {
        templateUrl: 'parameters.config.html',
        replace: true,
        scope: true,
        controller: parametersController,
        controllerAs: 'parametersCtl',
        link: parametersLink
    };
};

var Cleep = angular.module('Cleep');
Cleep.directive('parametersConfigDirective', ['toastService', 'parametersService', 'cleepService', '$timeout', parametersConfigDirective]);

