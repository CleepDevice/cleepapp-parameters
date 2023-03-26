/**
 * Parameters config component
 * Handle parameters configuration
 */
angular
.module('Cleep')
.directive('parametersConfigComponent', ['toastService', 'parametersService', 'cleepService', '$timeout',
function(toast, parametersService, cleepService, $timeout) {

    var parametersController = ['$scope', function($scope) {
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
        self.auth = {
            enabled: false,
            accounts: [],
        };
        self.newAccount = '';
        self.newPassword = '';

        /**
         * Set hostname
         */
        self.setHostname = function() {
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
        self.setPosition = function() {
            // check values
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
                .then(() => cleepService.reloadModuleConfig('parameters'))
                .then(function(config) {
                    self.updateConfig(config);
                    toast.success('Localisation saved');
                });
        };

        /**
         * Auth
         */
        self.toggleAuth = function() {
            const call = !self.auth.enabled ? parametersService.disableAuth : parametersService.enableAuth;
            call().then(() => cleepService.reloadModuleConfig('parameters'))
                .then((config) => {
                    self.updateConfig(config);
                    toast.success('Secured access updated');
                });
        };

        self.deleteAuthAccount = function(account) {
            parametersService.deleteAuthAccount(account)
                .then(() => cleepService.reloadModuleConfig('parameters'))
                .then((config) => {
                    self.updateConfig(config);
                    toast.success('Account deleted');
                });
        };

        self.addAuthAccount = function() {
            parametersService.addAuthAccount(self.newAccount, self.newPassword)
                .then(() => cleepService.reloadModuleConfig('parameters'))
                .then((config) => {
                    self.updateConfig(config);
                    self.newAccount = '';
                    self.newPassword = '';
                    toast.success('Account created');
                });
        };

        /**
         * Update controller config
         */
        self.updateConfig = function(config) {
            self.position = config.position;
            self.hostname = config.hostname;
            self.sun = config.sun;
            self.country = config.country;
            self.timezone = config.timezone;
            self.auth.enabled = config.authenabled;
            cleepService.syncVar(self.auth.accounts, config.authaccounts);
        };

        /**
         * Init controller
         */
        self.$onInit = function() {
            cleepService.getModuleConfig('parameters')
                .then(function(config) {
                    self.updateConfig(config);

                    // init leaflet
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

    return {
        templateUrl: 'parameters.config.html',
        replace: true,
        scope: true,
        controller: parametersController,
        controllerAs: 'parametersCtl',
    };
}]);

