import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './home.component.html',
  styleUrl: './home.component.css'
})
export class HomeComponent {
  features = [
    {
      icon: '🎤',
      title: 'Custom Rappers',
      description: 'Create battles with any rappers, real or fictional. Our AI captures their unique style and flow.'
    },
    {
      icon: '🎭',
      title: 'Multiple Styles',
      description: 'Choose from various rap styles: Old School, Trap, Conscious, Freestyle, and more.'
    },
    {
      icon: '👑',
      title: 'AI Judgment',
      description: 'Advanced AI analyzes verses and determines winners based on flow, wordplay, and delivery.'
    },
    {
      icon: '🔄',
      title: 'Multiple Rounds',
      description: 'Create battles with multiple rounds for extended lyrical warfare.'
    },
  ];
}