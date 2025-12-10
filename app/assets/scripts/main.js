// Import external dependencies
import './jquery_import';
import * as bootstrap from 'bootstrap';
import 'bootstrap-table';
import '../node_modules/bootstrap-table/dist/locale/bootstrap-table-nl-NL.min.js';
import '../node_modules/bootstrap-table/dist/extensions/cookie/bootstrap-table-cookie.min.js';
import '../node_modules/bootstrap-table/dist/extensions/sticky-header/bootstrap-table-sticky-header.min.js';
import L from 'leaflet';
import 'leaflet-geometryutil';
import 'leaflet.awesome-markers';
import 'leaflet.markercluster';

// Import local dependencies
import Router from './util/Router';
import common from './routes/common';
import home from './routes/home';
import map from './routes/map';


// Populate Router instance with DOM routes
const routes = new Router({
  // All pages
  common,
  // Home page
  home,
  // JS code for pages that show the map
  map,
});

// Load events
$(document).ready(() => routes.loadEvents());
