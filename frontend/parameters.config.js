/**
 * Parameters config component
 * Handle parameters configuration
 */
angular
.module('Cleep')
.directive('parametersConfigComponent', ['toastService', 'parametersService', 'cleepService',
function(toast, parametersService, cleepService) {

    var parametersController = ['$scope', function($scope) {
        var self = this;
        self.tabIndex = 'hostname';
        self.hostname = '';
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
         * Init controller
         */
        self.$onInit = function() {
            cleepService.getModuleConfig('parameters')
                .then(function(config) {
                    self.updateConfig(config, true);
                });
        };

        /**
         * Hostname
         */
        self.setHostname = function() {
            parametersService.setHostname(self.hostname)
                .then(function() {
                    return cleepService.reloadModuleConfig('parameters');
                })
                .then(function(config) {
                    self.updateConfig(config);
                    toast.success('Device name saved');
                })
                .catch(angular.noop);
        };

        /**
         * Position
         */
        self.setPosition = function(latitude, longitude) {
            if (typeof latitude !== 'number' || typeof longitude !== 'number'
                    || Number.isNaN(latitude) || Number.isNaN(longitude)) {
                toast.info('Please select position before setting position');
                return;
            }
            if (latitude === self.position.latitude && longitude === self.position.longitude) {
                toast.info('Position not changed');
                return;
            }

            toast.loading('Setting localisation...');
            parametersService.setPosition(latitude, longitude)
                .then(() => cleepService.reloadModuleConfig('parameters'))
                .then(function(config) {
                    self.updateConfig(config);
                    toast.success('Localisation saved');
                })
                .catch(angular.noop);
        };

        /**
         * Auth
         */
        self.setAuth = function (enabled) {
            const call = enabled ? parametersService.enableAuth : parametersService.disableAuth;
            call().then(() => cleepService.reloadModuleConfig('parameters'))
                .then((config) => {
                    self.updateConfig(config);
                    toast.success('Secured access updated');
                })
                .catch(() => {
                    // Switch already flipped via ng-model; restore backend state
                    self.auth.enabled = !enabled;
                });
        };

        self.deleteAuthAccount = function(account) {
            parametersService.deleteAuthAccount(account)
                .then(() => cleepService.reloadModuleConfig('parameters'))
                .then((config) => {
                    self.updateConfig(config, true);
                    toast.success('Account deleted');
                })
                .catch(angular.noop);
        };

        self.addAuthAccount = function() {
            parametersService.addAuthAccount(self.newAccount, self.newPassword)
                .then(() => cleepService.reloadModuleConfig('parameters'))
                .then((config) => {
                    self.updateConfig(config, true);
                    self.newAccount = '';
                    self.newPassword = '';
                    toast.success('Account created');
                })
                .catch(angular.noop);
        };

        /**
         * Update controller config
         */
        self.updateConfig = function(config, reloadAccounts=false) {
            self.position = config.position;
            self.hostname = config.hostname;
            self.sun = config.sun;
            self.country = config.country;
            self.timezone = config.timezone;
            self.auth.enabled = config.authenabled;

            if (reloadAccounts) {
                self.auth.accounts.splice(0, self.auth.accounts.length);
                for (const account of config.authaccounts) {
                    self.auth.accounts.push({
                        icon: 'account',
                        title: account,
                        clicks: [
                            { icon: 'delete', tooltip: 'Delete', click: self.deleteAuthAccount, meta: { account } },
                        ],
                    });
                }
            }
        };

    }];

    return {
        templateUrl: 'parameters.config.html',
        replace: true,
        scope: true,
        controller: parametersController,
        controllerAs: '$ctrl',
    };
}]);
