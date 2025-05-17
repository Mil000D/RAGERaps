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
      title: 'AI-Powered Verses',
      description: 'Generate authentic rap verses in the style of your favorite artists using cutting-edge AI technology.'
    },
    {
      icon: '🏆',
      title: 'Epic Battles',
      description: 'Set up battles between any rappers and watch them go head-to-head in a lyrical showdown.'
    },
    {
      icon: '🔥',
      title: 'Fair Judging',
      description: 'Our AI judges evaluate flow, rhyme schemes, wordplay, and punchlines to determine winners.'
    },
    {
      icon: '🎯',
      title: 'Custom Topics',
      description: 'Choose topics and styles to direct the battle in any direction you want.'
    }
  ];
}
