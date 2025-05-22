import { Routes } from '@angular/router';

import { HomeComponent } from './components/home/home.component';
import { BattleConfigComponent } from './components/battle-config/battle-config.component';
import { BattleArenaComponent } from './components/battle-arena/battle-arena.component';

export const routes: Routes = [
  { path: '', component: HomeComponent },
  { path: 'battle', component: BattleConfigComponent },
  { path: 'battle/arena/:id', component: BattleArenaComponent },
  { path: '**', redirectTo: '' }
];
