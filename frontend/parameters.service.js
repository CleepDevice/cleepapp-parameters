/**
 * Parameters service
 * Handle parameters module requests
 */
var parametersService = function($rootScope, rpcService, cleepService) {
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
        return rpcService.sendCommand('set_hostname', 'parameters', {'hostname':hostname});
    };

    /**
     * Set position
     */
    self.setPosition = function(lat, long) {
        return rpcService.sendCommand('set_position', 'parameters', {'latitude':lat, 'longitude':long}, 20);
    };

    /**
     * Catch time event
     */
    $rootScope.$on('parameters.time.now', function(event, uuid, params) {
        for( var i=0; i<cleepService.devices.length; i++ )
        {
            if( cleepService.devices[i].uuid==uuid )
            {
                cleepService.devices[i].timestamp = params.timestamp;
                cleepService.devices[i].sunset = params.sunset;
                cleepService.devices[i].sunrise = params.sunrise;
                break;
            }
        }
    });

};
    
var Cleep = angular.module('Cleep');
Cleep.service('parametersService', ['$rootScope', 'rpcService', 'cleepService', parametersService]);

