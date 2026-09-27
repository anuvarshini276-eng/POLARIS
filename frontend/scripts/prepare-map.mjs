import fs from 'node:fs';
import {feature} from 'topojson-client';
const world=JSON.parse(fs.readFileSync(new URL('../node_modules/world-atlas/land-110m.json',import.meta.url),'utf8'));
fs.writeFileSync(new URL('../public/land.geojson',import.meta.url),JSON.stringify(feature(world,world.objects.land)));
console.log('Prepared public-domain Natural Earth land geometry for the offline map.');
