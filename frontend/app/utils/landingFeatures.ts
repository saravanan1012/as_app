export type LandingFeature = {
  id: string
  title: string
  detail: string
}

/** Product story copy for the landing features section */
export const landingProductStory = {
  eyebrow: 'AS Napkins',
  headline: 'Cotton care, made for every day',
  body: 'Plant-based sanitary napkins crafted for comfort and protection — soft organic cotton against skin, thoughtful layers underneath, and a quiet ritual you can trust.',
  image: '/images/product-only.png',
  imageAlt: 'AS organic sanitary napkin'
}

export const landingFeatures: LandingFeature[] = [
  {
    id: 'organic-cotton',
    title: 'Organic cotton top sheet',
    detail: 'Soft, breathable contact layer designed for all-day comfort.'
  },
  {
    id: 'anion',
    title: 'Anion freshness strip',
    detail: 'Helps keep the surface feeling fresher through your day.'
  },
  {
    id: 'layers',
    title: 'Multi-layer absorption',
    detail: 'Layered core that draws moisture away while staying gentle.'
  },
  {
    id: 'wings',
    title: 'Secure wing fit',
    detail: 'Wings that hold in place so you can move with confidence.'
  },
  {
    id: 'plant-based',
    title: 'Plant-based materials',
    detail: 'Thoughtfully chosen materials for a cleaner care routine.'
  },
  {
    id: 'pouch',
    title: 'Everyday pouch ritual',
    detail: 'Discreet packaging made for your bag, drawer, or travel kit.'
  }
]
