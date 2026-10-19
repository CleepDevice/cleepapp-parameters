angular.module('Cleep').component('configMap', {
    template: `
        <div layout="column" layout-align="start stretch" id="{{ $ctrl.clId }}" class="config-item">
            <div layout="row" layout-align="space-between center">
                <config-item-desc
                    layout="row" layout-align="start-center"
                    cl-icon="$ctrl.clIcon" cl-icon-class="$ctrl.clIconClass"
                    cl-title="$ctrl.clTitle" cl-subtitle="$ctrl.clSubtitle">
                </config-item-desc>
                <config-item-save-button
                    cl-btn-icon="$ctrl.clBtnIcon" cl-btn-style="$ctrl.clBtnStyle" cl-btn-color="$ctrl.clBtnColor" cl-btn-click="$ctrl.onClick" cl-btn-tooltip="$ctrl.clBtnTooltip" cl-btn-disabled="$ctrl.clBtnDisabled"
                    cl-model="$ctrl.clModel" cl-meta="$ctrl.clMeta">
                </config-item-save-button>
            </div>
            <div flex>
                <leaflet center="$ctrl.position" defaults="$ctrl.defaults" height="{{ $ctrl.height }}"></leaflet>
            </div>
        </div>
    `,
    bindings: {
        clId: '@',
        clTitle: '@',
        clIcon: '@',
        clIconClass: '@',
        clBtnColor: '@',
        clBtnStyle: '@',
        clBtnIcon: '@',
        clBtnTooltip: '@',
        clMeta: '<?',
        clDisabled: '<?',
        clLatitude: '<',
        clLongitude: '<',
        clZoom: '<?',
        clMapHeight: '@?',
        clMapWidth: '@?',
        clClick: '&?',
    },
    controller: ['$scope', '$timeout', 'leafletData', function ($scope, $timeout, leafletData) {
        const ctrl = this;
        ctrl.position = {
            lat: 0,
            lng: 0,
            zoom: 8,
        };
        ctrl.defaults = {
            scrollWheelZoom: false,
            minZoom: 5,
            maxZoom: 12,
        };

        ctrl.invalidateMap = function () {
            $timeout(function () {
                leafletData.getMap().then(function (map) {
                    map.invalidateSize(false);
                }).catch(angular.noop);
            }, 0);
        };

        ctrl.$onInit = function () {
            ctrl.height = (ctrl.clMapHeight || ctrl.clMapWidth || '400') + 'px';
            // Tab panels may still be laying out on first paint
            ctrl.invalidateMap();
        };

        ctrl.$onChanges = function (changes) {
            if (changes.clLatitude?.currentValue) {
                ctrl.position.lat = changes.clLatitude.currentValue;
            }
            if (changes.clLongitude?.currentValue) {
                ctrl.position.lng = changes.clLongitude.currentValue;
            }
            if (changes.clZoom?.currentValue) {
                ctrl.position.zoom = changes.clZoom.currentValue;
            }
        };

        // config-tabs keeps inactive panels in the DOM (hidden). Leaflet must
        // recalculate when the panel that contains this map becomes visible.
        $scope.$on('config-tabs:shown', function () {
            ctrl.invalidateMap();
        });

        ctrl.onClick = function () {
            const data = {
                latitude: ctrl.position.lat,
                longitude: ctrl.position.lng,
            };
            (ctrl.clClick || angular.noop)(data);
        };
    }],
});
