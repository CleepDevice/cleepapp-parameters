/**
 * Parameters service
 * Handle parameters module requests
 */
angular
.module('Cleep')
.service('parametersService', ['$rootScope', 'rpcService', 'cleepService',
function($rootScope, rpcService, cleepService) {
    var self = this;
    
    /**
     * Get sunset/sunrise
     */
    self.getSun = function() {
        return rpcService.sendCommand('get_sun', 'parameters');
    };

    /**
     * Set hostname
     */
    self.setHostname = function(hostname) {
        return rpcService.sendCommand('set_hostname', 'parameters', { hostname });
    };

    /**
     * Set position
     */
    self.setPosition = function(latitude, longitude) {
        return rpcService.sendCommand('set_position', 'parameters', { latitude, longitude }, 30);
    };

    /**
     * Auth
     */
    self.enableAuth = function() {
        return rpcService.sendCommand('enable_auth', 'parameters');
    };

    self.disableAuth = function() {
        return rpcService.sendCommand('disable_auth', 'parameters');
    };

    self.addAuthAccount = function(account, password) {
        return rpcService.sendCommand('add_auth_account', 'parameters', { account, password });
    };

    self.deleteAuthAccount = function(account) {
        return rpcService.sendCommand('delete_auth_account', 'parameters', { account });
    };

    /**
     * Catch time event
     */
    $rootScope.$on('parameters.time.now', function(event, uuid, params) {
        for( var i=0; i<cleepService.devices.length; i++ )
        {
            if( cleepService.devices[i].uuid==uuid )
            {
                cleepService.devices[i].hour = params.hour;
                cleepService.devices[i].minute = params.minute;
                cleepService.devices[i].timestamp = params.timestamp;
                cleepService.devices[i].sunset = params.sunset;
                cleepService.devices[i].sunrise = params.sunrise;
                break;
            }
        }
    });

}]);

