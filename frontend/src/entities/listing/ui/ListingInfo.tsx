import { Badge } from '@/shared/ui/badge';
import { CITIES, STATUS_LABELS } from '@/shared/config';
import type { Listing } from '@/shared/types';
import { getListingPrice, getListingCurrency, getFirstImage } from '../model';

interface ListingInfoProps {
  listing: Listing;
}

export function ListingInfo({ listing }: ListingInfoProps) {
  const price = getListingPrice(listing);
  const currency = getListingCurrency(listing);
  const firstImage = getFirstImage(listing);
  const city = listing.city ? CITIES[listing.city as keyof typeof CITIES] : null;
  const statusLabel = STATUS_LABELS[listing.status as keyof typeof STATUS_LABELS];

  return (
    <div className="flex flex-col gap-2">
      {firstImage && (
        <img
          src={firstImage}
          alt={listing.title}
          className="w-full h-48 object-cover rounded-lg"
        />
      )}
      <h3 className="font-semibold text-lg">{listing.title}</h3>
      <div className="flex items-center gap-2">
        <Badge variant="secondary">{statusLabel}</Badge>
        {city && <Badge variant="outline">{city}</Badge>}
      </div>
      <p className="text-2xl font-bold">
        {price.toLocaleString()} {currency}
      </p>
      <div className="text-sm text-muted-foreground">
        {listing.rooms && <span>{listing.rooms}-комн • </span>}
        {listing.area && <span>{listing.area} м² • </span>}
        {listing.floor && <span>{listing.floor} этаж</span>}
      </div>
    </div>
  );
}
