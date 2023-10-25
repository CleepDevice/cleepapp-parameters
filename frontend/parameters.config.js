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
                .then(function(resp) {
                    return cleepService.reloadModuleConfig('parameters');
                })
                .then(function(config) {
                    self.updateConfig(config);
                    toast.success('Device name saved');
                });
        };

        /**
         * Position
         */
        self.setPosition = function(latitude, longitude) {
            // check values
            if (!latitude || !longitude) {
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
                });
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
                });
        };

        self.deleteAuthAccount = function(account) {
            parametersService.deleteAuthAccount(account)
                .then(() => cleepService.reloadModuleConfig('parameters'))
                .then((config) => {
                    self.updateConfig(config, true);
                    toast.success('Account deleted');
                });
        };

        self.addAuthAccount = function() {
            parametersService.addAuthAccount(self.newAccount, self.newPassword)
                .then(() => cleepService.reloadModuleConfig('parameters'))
                .then((config) => {
                    self.updateConfig(config, true);
                    self.newAccount = '';
                    self.newPassword = '';
                    toast.success('Account created');
                });
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

