/** Delivery locations matching pincodes in data/catalog-fixtures.json */
export type DeliveryLocation = {
  id: string;
  city: string;
  state: string;
  pincode: string;
  label: string;
};

export const DELIVERY_LOCATIONS: DeliveryLocation[] = [
  {
    id: "blr-560001",
    city: "Bangalore",
    state: "Karnataka",
    pincode: "560001",
    label: "Bangalore Central",
  },
  {
    id: "blr-560034",
    city: "Bangalore",
    state: "Karnataka",
    pincode: "560034",
    label: "Bangalore Koramangala",
  },
  {
    id: "del-110001",
    city: "New Delhi",
    state: "Delhi",
    pincode: "110001",
    label: "New Delhi Central",
  },
  {
    id: "mum-400001",
    city: "Mumbai",
    state: "Maharashtra",
    pincode: "400001",
    label: "Mumbai Fort",
  },
];
