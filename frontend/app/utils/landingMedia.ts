export type LandingMedia = {
  id: string
  type: 'image' | 'video'
  src: string
  alt: string
  poster?: string
  /** Mosaic span hint: tall | wide | square | portrait (9:16) */
  span?: 'tall' | 'wide' | 'square' | 'portrait'
}

/** Hero background — brand story reel */
export const landingHeroVideo = '/videos/sustainable-care.mp4'
export const landingHeroPoster = '/images/product-only.png'

/** Curated gallery (stills + selected videos). Paths under /public. */
export const landingGallery: LandingMedia[] = [
  {
    id: 'cotton-pouch',
    type: 'image',
    src: '/images/cotton-pouch.jpg',
    alt: 'Cotton pouch with organic sanitary napkin',
    span: 'wide'
  },
  {
    id: 'camera-orbit',
    type: 'video',
    src: '/videos/camera-orbit-a.mp4',
    poster: '/images/product-only.png',
    alt: 'Product orbit camera reel',
    span: 'tall'
  },
  {
    id: 'cream-display',
    type: 'image',
    src: '/images/cream-display.jpg',
    alt: 'Cream pouch and napkins display',
    span: 'square'
  },
  {
    id: 'hand-brushing',
    type: 'image',
    src: '/images/hand-brushing.jpg',
    alt: 'Hand brushing organic sanitary napkin',
    span: 'tall'
  },
  {
    id: 'drawstring',
    type: 'video',
    src: '/videos/drawstring-bag.mp4',
    poster: '/images/cotton-pouch.jpg',
    alt: 'Drawstring bag product video',
    span: 'portrait'
  },
  {
    id: 'anion-a',
    type: 'image',
    src: '/images/anion-strip-a.jpg',
    alt: 'Sanitary napkin with anion strip',
    span: 'square'
  },
  {
    id: 'drone-orbit',
    type: 'video',
    src: '/videos/drone-orbit-a.mp4',
    poster: '/images/pack-flat-a.jpg',
    alt: 'Drone orbit of napkin display',
    span: 'wide'
  },
  {
    id: 'pack-a',
    type: 'image',
    src: '/images/pack-flat-a.jpg',
    alt: 'Product pack flat lay',
    span: 'square'
  },
  {
    id: 'product-ad',
    type: 'video',
    src: '/videos/product-ad.mp4',
    poster: '/images/cream-display.jpg',
    alt: 'AS sanitary napkin product advertisement',
    span: 'tall'
  },
  {
    id: 'anion-b',
    type: 'image',
    src: '/images/anion-strip-b.jpg',
    alt: 'Close-up of anion strip detail',
    span: 'square'
  },
  {
    id: 'pack-b',
    type: 'image',
    src: '/images/pack-flat-b.jpg',
    alt: 'Alternate pack flat lay',
    span: 'wide'
  },
  {
    id: 'tamil-ad',
    type: 'video',
    src: '/videos/tamil-ad.mp4',
    poster: '/images/hand-brushing.jpg',
    alt: 'Tamil product advertisement',
    span: 'square'
  }
]
