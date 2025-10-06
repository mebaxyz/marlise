# MOD UI React CSS Structure Proposal

## Recommended File Organization

```
src/styles/
├── index.css                   # Main entry point
├── globals/
│   ├── reset.css              # CSS reset/normalize
│   ├── variables.css          # CSS custom properties
│   ├── typography.css         # Font definitions
│   └── utilities.css          # Utility classes
├── base/
│   ├── layout.css             # Core layout patterns
│   ├── grid.css               # Grid system
│   └── responsive.css         # Breakpoints & media queries
├── components/
│   ├── buttons/
│   │   ├── Button.css
│   │   ├── IconButton.css
│   │   └── ToggleButton.css
│   ├── forms/
│   │   ├── Input.css
│   │   ├── Select.css
│   │   └── Checkbox.css
│   ├── navigation/
│   │   ├── MainMenu.css
│   │   ├── Breadcrumb.css
│   │   └── Tabs.css
│   ├── modals/
│   │   ├── Modal.css
│   │   ├── Dialog.css
│   │   └── Tooltip.css
│   ├── cards/
│   │   ├── PluginCard.css
│   │   ├── PedalboardCard.css
│   │   └── BankCard.css
│   ├── lists/
│   │   ├── PluginList.css
│   │   ├── PedalboardList.css
│   │   └── BankList.css
│   └── controls/
│       ├── Knob.css
│       ├── Switch.css
│       ├── Slider.css
│       └── Addressing.css
├── layout/
│   ├── Header.css             # Top navigation/actions
│   ├── MainMenu.css           # Bottom main menu
│   ├── Sidebar.css            # Side panels
│   └── Footer.css             # Status bar
├── pages/
│   ├── Pedalboard.css         # Main pedalboard view
│   ├── PluginLibrary.css      # Plugin browser
│   ├── PedalboardLibrary.css  # Pedalboard browser
│   ├── BankLibrary.css        # Bank management
│   ├── Settings.css           # Settings panel
│   └── FileManager.css        # File management
├── themes/
│   ├── default.css            # Default MOD theme
│   ├── dark.css               # Dark theme variant
│   └── high-contrast.css      # Accessibility theme
└── vendor/
    ├── bootstrap-grid.css     # Minimal Bootstrap grid only
    └── normalize.css          # Browser normalization
```

## Key Files Content

### 1. variables.css - CSS Custom Properties
```css
:root {
  /* Colors */
  --mod-primary: #883996;
  --mod-primary-dark: #662b71;
  --mod-primary-light: #a144b2;
  --mod-background: #111;
  --mod-surface: #2c2c2c;
  --mod-accent: #f29446;
  --mod-success: #dff0d8;
  --mod-warning: #f29446;
  --mod-error: #d9534f;
  --mod-text-primary: #ffffff;
  --mod-text-secondary: #999999;
  --mod-text-disabled: #666666;
  
  /* Spacing */
  --mod-spacing-xs: 4px;
  --mod-spacing-sm: 8px;
  --mod-spacing-md: 16px;
  --mod-spacing-lg: 24px;
  --mod-spacing-xl: 32px;
  --mod-spacing-xxl: 48px;
  
  /* Typography */
  --mod-font-family: "Cooper Hewitt", sans-serif;
  --mod-font-size-xs: 10px;
  --mod-font-size-sm: 12px;
  --mod-font-size-base: 14px;
  --mod-font-size-lg: 16px;
  --mod-font-size-xl: 18px;
  --mod-font-size-xxl: 24px;
  
  /* Layout */
  --mod-header-height: 45px;
  --mod-footer-height: 45px;
  --mod-sidebar-width: 240px;
  --mod-plugin-strip-height: 166px;
  
  /* Shadows */
  --mod-shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.12);
  --mod-shadow-md: 0 4px 6px rgba(0, 0, 0, 0.16);
  --mod-shadow-lg: 0 10px 20px rgba(0, 0, 0, 0.19);
  --mod-shadow-pedal: 2px 8px 7px rgba(0, 0, 0, 0.2),
                      4px 16px 7px rgba(0, 0, 0, 0.2),
                      6px 24px 7px rgba(0, 0, 0, 0.2),
                      8px 32px 7px rgba(0, 0, 0, 0.2),
                      10px 40px 7px rgba(0, 0, 0, 0.2),
                      5px 20px 50px rgba(0, 0, 0, 0.9);
  
  /* Transitions */
  --mod-transition-fast: 0.15s ease;
  --mod-transition-normal: 0.33s ease;
  --mod-transition-slow: 0.5s ease;
  
  /* Borders */
  --mod-border-radius: 0px; /* MOD uses sharp corners */
  --mod-border-width: 1px;
  --mod-border-color: #333;
  
  /* Z-index layers */
  --z-modal: 1000;
  --z-dropdown: 100;
  --z-header: 10;
  --z-footer: 10;
  --z-content: 1;
}
```

### 2. layout.css - Core Layout Patterns
```css
/* Core Layout System */
.mod-layout {
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.mod-header {
  height: var(--mod-header-height);
  background: var(--mod-background);
  border-bottom: 1px solid var(--mod-border-color);
  z-index: var(--z-header);
}

.mod-main {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.mod-content {
  flex: 1;
  background: var(--mod-background);
  position: relative;
}

.mod-footer {
  height: var(--mod-footer-height);
  background: var(--mod-background);
  border-top: 1px solid var(--mod-border-color);
  z-index: var(--z-footer);
}

/* Pedalboard Layout */
.mod-pedalboard-view {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.mod-pedalboard-container {
  flex: 1;
  background: var(--mod-background) url('../assets/img/background.jpg') repeat;
  background-size: auto 1200px;
  position: relative;
  overflow: auto;
}

.mod-plugin-constructor {
  height: var(--mod-plugin-strip-height);
  background: rgba(17, 17, 17, 0.9);
  border-top: 1px solid var(--mod-border-color);
}

/* Plugin Strip Layout */
.plugin-list-horizontal {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.plugin-list-header {
  height: 38px;
  background: rgba(17, 17, 17, 0.66);
  display: flex;
  align-items: center;
  padding: 0 var(--mod-spacing-sm);
}

.plugin-list-content {
  flex: 1;
  display: flex;
  align-items: flex-start;
  overflow-x: auto;
  overflow-y: hidden;
  padding: var(--mod-spacing-sm);
  gap: var(--mod-spacing-sm);
}

/* Responsive Breakpoints */
@media (max-width: 768px) {
  .plugin-list-content {
    flex-direction: column;
    overflow-x: hidden;
    overflow-y: auto;
  }
}
```

### 3. PluginCard.css - Reusable Plugin Components
```css
/* Plugin Card Base */
.plugin-card {
  background: rgba(255, 255, 255, 0.07);
  color: var(--mod-text-primary);
  border: 1px solid transparent;
  transition: var(--mod-transition-normal);
  cursor: pointer;
  user-select: none;
}

.plugin-card:hover {
  background: var(--mod-primary);
  border-color: var(--mod-primary-light);
}

/* Horizontal Plugin Cards (for strip) */
.plugin-card-horizontal {
  width: 120px;
  height: 108px;
  padding: var(--mod-spacing-sm);
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.plugin-card-horizontal .plugin-thumb {
  height: 64px;
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: var(--mod-spacing-xs);
}

.plugin-card-horizontal .plugin-thumb img {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
}

.plugin-card-horizontal .plugin-title {
  font-size: var(--mod-font-size-xs);
  font-weight: bold;
  line-height: 1.2;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  width: 100%;
}

.plugin-card-horizontal .plugin-author {
  font-size: var(--mod-font-size-xs);
  color: var(--mod-text-secondary);
  line-height: 1;
}

/* Vertical Plugin Cards (for lists) */
.plugin-card-vertical {
  display: flex;
  align-items: center;
  padding: var(--mod-spacing-sm);
  margin-bottom: 1px;
  min-height: 48px;
}

.plugin-card-vertical .plugin-thumb {
  width: 48px;
  height: 32px;
  margin-right: var(--mod-spacing-sm);
  flex-shrink: 0;
}

.plugin-card-vertical .plugin-info {
  flex: 1;
  min-width: 0;
}

.plugin-card-vertical .plugin-title {
  font-weight: bold;
  margin-bottom: 2px;
}

.plugin-card-vertical .plugin-author {
  font-size: var(--mod-font-size-sm);
  color: var(--mod-text-secondary);
}

/* Plugin Status Indicators */
.plugin-status {
  position: absolute;
  top: var(--mod-spacing-xs);
  right: var(--mod-spacing-xs);
  font-size: var(--mod-font-size-xs);
  padding: 2px 4px;
  border-radius: 2px;
  font-weight: bold;
  text-transform: uppercase;
}

.plugin-status.installed {
  background: var(--mod-success);
  color: var(--mod-background);
}

.plugin-status.demo {
  background: var(--mod-warning);
  color: var(--mod-background);
}

/* Drag and Drop States */
.plugin-card.dragging {
  opacity: 0.5;
  transform: rotate(5deg);
}

.plugin-card.drag-over {
  border-color: var(--mod-accent);
  background: rgba(242, 148, 70, 0.2);
}
```

### 4. MainMenu.css - Bottom Navigation
```css
/* Main Menu Bar */
.main-menu {
  height: var(--mod-footer-height);
  background: var(--mod-background);
  display: flex;
  align-items: center;
  border-top: 1px solid var(--mod-border-color);
}

.main-menu-item {
  width: 45px;
  height: 45px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: var(--mod-transition-normal);
  background-size: 24px;
  background-position: center;
  background-repeat: no-repeat;
}

.main-menu-item:hover {
  background-color: #000;
}

.main-menu-item.active {
  background-color: #000;
}

/* Menu Icons */
.main-menu-item.plugins {
  background-image: url('../assets/img/menu-icons-sprite.png');
  background-position: -45px top;
}

.main-menu-item.plugins:hover,
.main-menu-item.plugins.active {
  background-position: -45px bottom;
}

.main-menu-item.pedalboards {
  background-image: url('../assets/img/menu-icons-sprite.png');
  background-position: -90px top;
}

.main-menu-item.pedalboards:hover,
.main-menu-item.pedalboards.active {
  background-position: -90px bottom;
}

/* Status Indicators */
.main-menu-status {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 1px;
}

.status-item {
  height: 45px;
  padding: 0 var(--mod-spacing-sm);
  display: flex;
  align-items: center;
  font-size: var(--mod-font-size-xs);
  color: var(--mod-text-primary);
  text-transform: uppercase;
  font-weight: bold;
  background-position: 8px center;
  background-repeat: no-repeat;
  background-size: 20px;
  padding-left: 35px;
}

.status-item.cpu {
  background-image: url('../assets/img/icons/25/cpu.png');
}
```

## Implementation Strategy

### Phase 1: Foundation (Week 1)
1. Set up the new CSS structure
2. Implement CSS variables and base styles
3. Create core layout components
4. Migrate existing components to new structure

### Phase 2: Components (Week 2)
1. Implement plugin card variations
2. Create main menu system
3. Build modal and dialog components
4. Add form controls and inputs

### Phase 3: Pages & Features (Week 3)
1. Implement page-specific styles
2. Add responsive behavior
3. Create theme variants
4. Optimize performance

### Phase 4: Polish (Week 4)
1. Add animations and transitions
2. Implement accessibility features
3. Cross-browser testing
4. Documentation

## Key Benefits of This Structure

1. **Modularity**: Each component has its own CSS file
2. **Maintainability**: Clear separation of concerns
3. **Scalability**: Easy to add new components
4. **Consistency**: CSS variables ensure consistent theming
5. **Performance**: Tree-shaking unused CSS
6. **Developer Experience**: Clear file organization
7. **Responsive**: Mobile-first approach with breakpoints
8. **Accessibility**: WCAG-compliant color contrasts and focus states

## Migration Path

1. **Gradual Migration**: Convert components one at a time
2. **CSS Modules**: Use CSS modules for component isolation
3. **CSS-in-JS Alternative**: Consider styled-components for dynamic theming
4. **Build Optimization**: Use PostCSS for autoprefixing and optimization
5. **Testing**: Visual regression tests for UI consistency

This structure provides a solid foundation for maintaining and scaling the MOD UI React application while preserving the original design system and user experience.