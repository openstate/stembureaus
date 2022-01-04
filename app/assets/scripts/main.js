// Import external dependencies
import 'jquery';
import 'bootstrap-sass';
import 'bootstrap-table'
import 'floatthead';
import L from 'leaflet';
import 'leaflet.awesome-markers';
import 'leaflet.markercluster';

// Import local dependencies
import Router from './util/Router';
import common from './routes/common';
import home from './routes/home';
import map from './routes/map';


// Import the needed Font Awesome functionality
import { config, library, dom } from '@fortawesome/fontawesome-svg-core';
// Import required icons
import { faPencilAlt, faEnvelope, faExternalLinkAlt, faQuestionCircle, faWheelchair, faBan, faDeaf, faCode, faMapMarkerAlt, faSearch, faCheck } from '@fortawesome/free-solid-svg-icons';
import { faTwitter, faLinkedin, faFacebookF, faGithub } from '@fortawesome/free-brands-svg-icons';
import { faEnvelope as faEnvelopeR } from '@fortawesome/free-regular-svg-icons';

// Add the imported icons to the library
library.add(faPencilAlt, faEnvelope, faExternalLinkAlt, faQuestionCircle, faWheelchair, faBan, faDeaf, faCode, faLinkedin, faTwitter, faFacebookF, faGithub, faEnvelopeR, faMapMarkerAlt, faSearch, faCheck);

// Tell FontAwesome to watch the DOM and add the SVGs when it detects icon markup
dom.watch();

// Allows us to use jQuery in <script> elements in the .html files
global.$ = global.jQuery = require('jquery');

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
